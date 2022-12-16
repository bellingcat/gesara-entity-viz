# GESARA Named Entity Network Visualization

This project generates an [interactive visualization](https://bellingcat.github.io/gesara-entity-viz/) of [named entities](https://spacy.io/usage/linguistic-features#named-entities) in English-language posts archived in a database of Telegram channels that have posted about the GESARA conspiracy theory.

This visualization was developed by Bellingcat based on an excellent [Sigma.js demo](https://github.com/jacomyal/sigma.js/tree/main/demo), and uses [react-sigma-v2](https://github.com/sim51/react-sigma-v2) to interface sigma.js with React.

You can view the live visualization [here](https://bellingcat.github.io/gesara-entity-viz/). With GitHub pages configured, after making changes to the `main` branch, you need th run the command `npm run deploy` for the latest changes to be reflected in the live visualization.

## Python Scripts

In the `scripts/` subdirectory, you can run Python scripts that were used to generate the network and visualization:

### `generate_network.py`

Extracts the data from a PostgreSQL database, cleans the entity data, generates a NetworkX graph, prunes the edges using the [Marginal Likelihood Filter](https://github.com/naviddianati/GraphPruning), and exports the pruned graph.

### `generate_visualization.py`

After visualizing the network using [Gephi](https://gephi.org/) (using the Force Atlas 2 algorithm, with the "LinLog mode" and "Prevent Overlap" options enabled, and exporting as the file `entity_network_layout.graphml`), this script converts the node, edge, and cluster data into a format readable by this sigma.js project.

## NPM Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:5000](http://localhost:5000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.
