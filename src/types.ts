import { Extent } from "sigma/types";

export interface NodeData {
  key: string;
  label: string;
  cluster: string;
  x: number;
  y: number;
  size: number;
}

export interface Cluster {
  key: string;
  color: string;
  clusterLabel: string;
}

export interface Dataset {
  nodes: NodeData[];
  edges: [string, string][];
  clusters: Cluster[];
  bbox: {'x': Extent, 'y': Extent},
  labelThreshold: number
}

export interface FiltersState {
  clusters: Record<string, boolean>;
}
