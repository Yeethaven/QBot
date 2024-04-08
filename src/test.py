import networkx as nx
import pickle

filepath = "./data/test.graphml"

def t1():
    scoreboard = nx.DiGraph()
    scoreboard.add_edge(123456, 654321, weight=5)
    print(scoreboard.has_edge(123456, 654321))
    print(scoreboard[123456][654321]['weight'])

    #nx.write_multiline_adjlist(scoreboard, filepath)
    #scoreboard = nx.read_multiline_adjlist(filepath)

    pickle.dump(scoreboard, open(filepath, 'wb'))
    scoreboard = pickle.load(open(filepath, 'rb'))
    
    print(scoreboard.has_edge(123456, 654321))
    print(scoreboard[123456][654321]['weight'])

def t2():
    arr1 = [1, 2, 3]
    arr2 = [[4, 5, 6], [7, 8, 9]]
    arr3 = [arr1] + arr2
    print(arr3)

if __name__ == "__main__":
    t2()