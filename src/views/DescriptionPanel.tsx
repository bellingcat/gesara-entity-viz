import React, { FC } from "react";
import { BsInfoCircle } from "react-icons/bs";

import Panel from "./Panel";

const DescriptionPanel: FC = () => {
  return (
    <Panel
      initiallyDeployed
      title={
        <>
          <BsInfoCircle className="text-muted" /> Description
        </>
      }
    >
      <p>
        This visualisation represents a <i>network</i> of{" "}
        <a target="_blank" rel="noreferrer" href="https://spacy.io/usage/linguistic-features#named-entities">
          named entities
        </a> in English-language posts archived in a database of Telegram channels that have posted about the GESARA conspiracy theory. Each{" "}
        <i>node</i> represents an entity, <i>edges</i> between nodes indicate that one or more posts contain both entities
        .
      </p>
      <p>
        This kind of visualization shows the ecosystem of the people, organizations, and ideas these conspiracy Telegram channels talk about, as well as the connections between them.
      </p>
      <p>
        Some social media channels were identified by researchers from{" "}
        <a target="_blank" rel="noreferrer" href="https://www.bellingcat.com/">
          Bellingcat
        </a>{" "}and{" "}
        <a target="_blank" rel="noreferrer" href="https://www.lighthousereports.nl/">
          Lighthouse Reports
        </a>
        , then several rounds of snowball sampling found forwarded channels that have posted about GESARA.
        The entities were identified using {" "}
        <a target="_blank" rel="noreferrer" href="https://spacy.io/">
          spaCy
        </a>
        .
      </p>
      <p>
        This web application has been developed by{" "}
        <a target="_blank" rel="noreferrer" href="https://www.bellingcat.com/">
          Bellingcat
        </a>
        , using{" "}
        <a target="_blank" rel="noreferrer" href="https://reactjs.org/">
          react
        </a>{" "}
        and{" "}
        <a target="_blank" rel="noreferrer" href="https://www.sigmajs.org">
          sigma.js
        </a>
        . You can read the source code{" "}
        <a target="_blank" rel="noreferrer" href="https://github.com/bellingcat/gesara-entity-viz">
          on GitHub
        </a>
        .
      </p>
      <p>
        The network was visualized using{" "}
        <a target="_blank" rel="noreferrer" href="https://gephi.org/">
        Gephi
        </a>. Node sizes are related to the number of channels the entity was posted about in the database.
        Nodes are colored based a{" "}
        <a target="_blank" rel="noreferrer" href="https://arxiv.org/abs/0803.0476">
        community detection algorithm
        </a>.
        For visualisation purposes, edges were pruned using the{" "}
        <a target="_blank" rel="noreferrer" href="https://github.com/naviddianati/GraphPruning">
          Marginal Likelihood Filter
        </a>
        .
      </p>
    </Panel>
  );
};

export default DescriptionPanel;
