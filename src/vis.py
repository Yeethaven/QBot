import networkx as nx
import holoviews as hv
from holoviews import opts
import json
from variables import namefile

def visualize(G:nx.DiGraph):
    hv.extension('bokeh')
    edges = nx.to_pandas_edgelist(G, edge_key='weight')
    with open(namefile, "r") as file:
            names = json.load(file)
    edges['source'] = edges['source'].astype(str).map(names)
    edges['target'] = edges['target'].astype(str).map(names)
    edges['weight'] = edges['weight'].astype(int)
    
    chord = hv.Chord(edges, vdims='weight')
    chord.opts(opts.Chord(
         cmap = 'Category20',  # categorical color scheme
          edge_cmap = 'Category20',  # categorical color scheme
          labels = 'index',  # labels based on the index
          node_color = hv.dim('index').str(), # node colour based on index
          edge_color = hv.dim('source').str(), # edge colour based on the source, here: event_type)
          width = 500,
          height = 500))
    hv.save(chord, "./data/plot.png")

if __name__ == "__main__":
    from pickle import load
    from variables import filepath
    scoreboard = load(open(filepath, 'rb'))
    visualize(scoreboard)
