import os
import re
from itertools import chain, combinations
from collections import Counter
from pathlib import Path
import json
from functools import cache

import sqlalchemy
import pandas as pd
import networkx as nx

import emoji
from unidecode import unidecode
import igraph as ig
import numpy as np
import nltk

# https://github.com/naviddianati/GraphPruning
from pruning import unimodal


# SQL connection string to database
CONNECTION_STRING = os.environ["GESARA_DB"]
# SQL query to retrieve English-language named entities for each post
SQL_QUERY = """
SELECT channel, string_agg(entity_text, '|') as named_entities FROM 
    (SELECT id, 
    channel,
    json_array_elements(named_entities) ->> 'type' AS entity_type, 
    json_array_elements(named_entities) ->> 'text' AS entity_text 
    FROM posts 
    WHERE detected_language = 'en' 
    AND json_array_length(named_entities) > 0) tmp
WHERE entity_type IN ('ORG', 'PERSON')
GROUP BY id, channel;
"""
# Directory containing input and output data
DATA_DIR = Path("./data")
# JSON file containing entity replacement terms
CONSOLIDATION_JSON = DATA_DIR / "entity_consolidation.json"
# JSON file containing information about entities to ignore during consolidation
IGNORE_CONSOLIDATION_JSON = DATA_DIR / "ignore_consolidation.json"

# Ignore entities that are stopwords in common languages
STOPWORD_LANGUAGES = [
    "danish",
    "dutch",
    "english",
    "french",
    "german",
    "italian",
    "portuguese",
    "russian",
    "spanish",
]

# Ignore entities mentioned in fewer than this many posts in database
POST_FREQUENCY_THRESHOLD = 200
# Ignore entities mentioned by fewer than this many channels in database
CHANNEL_FREQUENCY_THRESHOLD = 175
# Ignore edges between entities co-occurring in fewer than this many posts
EDGE_WEIGHT_THRESHOLD = 10
# Prune away this percent of the least significant edges
PRUNING_PERCENTILE = 90

# GraphML file to write network data to
OUTPUT_GRAPHML = DATA_DIR / f"entity_network.graphml"


def create_replacement_dict():
    """Load JSON file containing entity replacements (e.g. "donald j trump" and "djt" both refer to the same person) and create dict for renaming entities."""

    with open(CONSOLIDATION_JSON, "r") as f:
        entity_consolidation = json.load(f)

    replacement_dict = {}
    for original, replacement_list in entity_consolidation.items():
        for replacement in replacement_list:
            replacement_dict[replacement] = original

    return replacement_dict


def create_ignore_list():
    """Create list of entities to ignore."""

    ignore_entities = set(
        chain.from_iterable(
            [nltk.corpus.stopwords.words(language) for language in STOPWORD_LANGUAGES]
        )
    )

    return ignore_entities


replacement_dict = create_replacement_dict()


def create_consolidation_dict(results):
    """Some entities are actually two or more entities separated by a "&" or ",". There are also plural versions of some entities, which results in redundancy. This function creates a dict that maps entities to their replacement, for example changing `'fauci & bill gates'` to `['anthony fauci', 'bill gates']`.

    1. Load JSON file containing information about which entities to consolidate
    2. Find all redundant plural entities
    3. Find all entities separated by comman, ampersand, and dash
    """

    with open(IGNORE_CONSOLIDATION_JSON, "r") as f:
        ignore_consolidation = json.load(f)
    ignore_plurals = set(ignore_consolidation["plurals"])
    ignore_separations = set(ignore_consolidation["separations"])
    consolidation_dict = ignore_consolidation["starting"]

    unique_entities = set(chain.from_iterable(results["valid_entities"]))
    replaced_entities = set(replacement_dict.keys())

    for entity in unique_entities:
        if (entity in ignore_plurals) or (entity in consolidation_dict):
            continue
        elif (len(entity) > 3) & (entity.endswith("s")):
            if (entity + "s") in replaced_entities:
                consolidation_dict[entity] = [replacement_dict[entity[:-1]]]
            elif (entity[:-1]) in unique_entities:
                consolidation_dict[entity] = [entity[:-1]]

    for character in [",", "&", "-"]:
        for entity in unique_entities:
            _entity = entity.replace(f" {character} ", character)
            if (entity in ignore_separations) or (entity in consolidation_dict):
                continue
            elif (character in _entity) & (len(_entity) > 4):
                terms = [term.strip() for term in _entity.split(character)]
                transformed_terms = []
                for term in terms:
                    if term in replaced_entities:
                        transformed_terms.append(replacement_dict[term])
                    elif term in unique_entities:
                        transformed_terms.append(term)
                    else:
                        transformed_terms = []
                        break
                if transformed_terms:
                    consolidation_dict[entity] = transformed_terms

    return consolidation_dict


def consolidate_entities(entities, consolidation_dict):
    """Apply the dict generated by `create_consolidation_dict` to a list of entities"""

    new_entities = []
    for entity in entities:
        new_entity = consolidation_dict.get(entity, [entity])
        new_entities.extend(new_entity)
    return set(new_entities)


@cache
def process_entity(s):
    """All-purpose text cleaning of very dirty entities list"""

    _s = unidecode(s).lower()

    if any([bad in _s for bad in ["http", "www.", "t.me", ">>", "@", "/", ">"]]):
        return None
    if _s.startswith("@"):
        return None
    if len(emoji.emoji_list(_s)) > 0:
        return None
    if len(re.findall("[\U0001F1E6-\U0001F1FF]", _s)) > 0:
        return None
    if len(re.findall(r"^[^a-zA-Z0-9]$", _s)) == 1:
        return None

    _s = re.sub("\s\s+", " ", _s)

    if _s.endswith("'s"):
        _s = "'s".join(_s.split("'s")[:-1])
    if _s.endswith("’s"):
        _s = "'s".join(_s.split("’s")[:-1])
    if _s.endswith("'"):
        _s = "'".join(_s.split("'")[:-1])
    if _s.startswith("the"):
        _s = "the".join(_s.split("the")[1:])
    if _s.startswith("now - "):
        _s = "now - ".join(_s.split("now - ")[1:])
    if _s.startswith("new - "):
        _s = "new - ".join(_s.split("new - ")[1:])
    if _s.startswith("in - "):
        _s = "in - ".join(_s.split("in - ")[1:])
    if _s.startswith('"'):
        _s = '"'.join(_s.split('"')[1:])
    if _s.startswith("'"):
        _s = "'".join(_s.split("'")[1:])
    if _s.startswith("a "):
        _s = "a ".join(_s.split("a ")[1:])
    if _s.startswith("inbox -"):
        _s = "inbox -".join(_s.split("inbox -")[1:])
    if _s.endswith("- telegram"):
        _s = "- telegram".join(_s.split("- telegram")[:-1])
    _s = _s.replace("\xa0", " ")

    for bad in ")(…º×•#:|[]":
        _s = _s.replace(bad, "")
    for bad in ["\n"]:
        _s = _s.replace(bad, " ")
    _s = _s.replace("\u2800", " ")
    _s = _s.replace("u.s.", "us")
    _s = _s.replace("u s.", "us")
    _s = _s.replace("u.n.", "un")

    _s = _s.strip('&"\'".!-,*~+= ')

    if _s.startswith('"'):
        if _s.count('"') % 2 == 1:
            _s = _s[1:]
    if _s.startswith("'"):
        if _s.count("'") % 2 == 1:
            _s = _s[1:]
    for pattern in [r"(\d+)(a|p)m", r"(\d+)"]:
        if re.findall(pattern, _s):
            return None

    entity = unidecode(_s).strip().lower()

    if renamed_entity := replacement_dict.get(entity):
        return renamed_entity
    else:
        if len(entity) <= 2:
            return None
        else:
            return entity


def process_entities(el):
    """Clean all entities in the list of entities"""

    return set(filter(None, [process_entity(d) for d in el.split("|")]))


def retrieve_data():
    """Retrieve English-language named entities from database and clean data.

    1. Inititalize SQL connection
    2. Retrieve English-language named entities grouped by post
    3. Process each list of named entities
    """

    engine = sqlalchemy.create_engine(url=CONNECTION_STRING)
    results = pd.read_sql(sql=SQL_QUERY, con=engine)
    results["named_entities"] = results["named_entities"].apply(process_entities)

    return results


def create_edge_list(results):
    """Create an edge list from the named entity data.

    1. Ignore entities that are mentioned less than `POST_FREQUENCY_THRESHOLD` times in the database or are stopwords in other languages
    2. Create list of co-occurring, frequently-mentioned entities
    3. Loop through all (sorted and unique) combinations of co-occurring entities to generate edge list
    """

    ignore_list = create_ignore_list()

    all_entities = list(chain.from_iterable(results["named_entities"]))
    c = Counter(all_entities)
    valid_entities = (
        set(
            [
                entity
                for entity, frequency in c.items()
                if frequency >= POST_FREQUENCY_THRESHOLD
            ]
        )
        - ignore_list
    )

    _valid_entity_lists = [
        [entity for entity in entity_set if entity in valid_entities]
        for entity_set in results["named_entities"]
    ]
    valid_entity_lists = [
        entity_list for entity_list in _valid_entity_lists if len(entity_list) > 1
    ]
    valid_entity_idxs = [
        True if len(entity_list) > 1 else False for entity_list in _valid_entity_lists
    ]

    results = results[valid_entity_idxs][["channel"]]
    results["valid_entities"] = valid_entity_lists

    consolidation_dict = create_consolidation_dict(results=results)
    results["valid_entities"] = results["valid_entities"].apply(
        lambda entities: consolidate_entities(
            entities=entities, consolidation_dict=consolidation_dict
        )
    )

    entity_n_channels = dict(
        results[["channel", "valid_entities"]]
        .explode("valid_entities")
        .groupby("valid_entities")["channel"]
        .nunique()
    )

    results["entity_tuples"] = results["valid_entities"].apply(
        lambda entity_list: list(
            tuple(sorted(combo)) for combo in combinations(entity_list, r=2)
        )
    )

    edf = results[["channel", "entity_tuples"]].explode("entity_tuples")
    grouped = edf.groupby("entity_tuples")["channel"].count()

    edge_list = [
        (source, target, weight)
        for (source, target), weight in zip(grouped.index, grouped.values)
        if weight > EDGE_WEIGHT_THRESHOLD
    ]

    return edge_list, entity_n_channels


def create_and_filter_graph(edge_list, entity_frequency, pruning_percentile):
    """Create a network from an edge list.

    1. Initialize a graph from the specified edge list and remove unconnected components
    2. Convert from NetworkX to igraph format, apply Marginal Likelihood Filter (MLF)
    3. Prune edges of the graph to a specified significance percentile and convert back to NetworkX format
    4. Set node attributes and remove unconnected components
    """

    G = nx.Graph()
    G.add_weighted_edges_from(edge_list)
    nodes_to_remove = [
        entity
        for entity, frequency in entity_frequency.items()
        if frequency <= CHANNEL_FREQUENCY_THRESHOLD
    ]
    G.remove_nodes_from(nodes_to_remove)
    G = G.subgraph(max(nx.connected_components(G), key=len))

    h = ig.Graph.from_networkx(G)
    mlf = unimodal.MLF(directed=False)
    H = mlf.fit_transform(h)

    df_edges = H.get_edge_dataframe()
    df_nodes = H.get_vertex_dataframe()
    node_id_to_name = dict(zip(df_nodes.index, df_nodes.values.flatten()))

    filtered_edgelist = []

    for _, t in df_edges[
        df_edges["significance"]
        >= np.percentile(a=df_edges["significance"], q=pruning_percentile)
    ].iterrows():
        edge = (
            node_id_to_name[t["source"]],
            node_id_to_name[t["target"]],
            t["weight"],
        )
        filtered_edgelist.append(edge)

    J = nx.Graph()
    J.add_weighted_edges_from(filtered_edgelist)
    nodes_set = set(J.nodes)
    _entity_frequency = {k: v for k, v in entity_frequency.items() if k in nodes_set}
    nx.set_node_attributes(G=J, values=_entity_frequency, name="frequency")
    J = J.subgraph(max(nx.connected_components(J), key=len))

    return J


if __name__ == "__main__":

    results = retrieve_data()
    edge_list, entity_frequency = create_edge_list(results=results)
    J = create_and_filter_graph(
        edge_list=edge_list,
        entity_frequency=entity_frequency,
        pruning_percentile=PRUNING_PERCENTILE,
    )

    nx.write_graphml(G=J, path=OUTPUT_GRAPHML)
