import math


from Chessnut import Game
from Chessnut.board import Board
import networkx as nx
import matplotlib.pyplot as plt


base_node = ' '.join(Game.default_fen.split()[:3])

class MyGame(Game):
    def apply_moves(self,moves):
        for move in moves:
            self.apply_move(move)
            
    @property
    def alg_move_history(self):
        moves = self.move_history
        fens = self.fen_history
        a_moves = []
        for x in range(len(moves)):
            s1 = moves[x][:2]
            s2 = moves[x][2:]
            i1 = self.xy2i(s1)
            i2 = self.xy2i(s2)
            b = Board(fens[x])
            p1 = b.get_piece(i1)
            p2 = b.get_piece(i2)
            if p2 == ' ':
                if p1.upper() == 'P':
                    a_move = s2
                elif p1.upper() == 'K' and abs(i1-i2)==2:
                    a_move = 'O-O-O' if s2[0]=='c' else 'O-O'
                else:
                    a_move = p1.upper()+s2
            else:
                if p1.upper() == 'P':
                    a_move = s1[0]+'x'+s2
                else:
                    a_move = p1.upper()+'x'+s2
            a_moves.append(a_move)
        return a_moves
    
#    @property
#    def trimmed_fen_history(self):
#        return [' '.join(f.split()[:3]) for f in self.fen_history]
            
            

class ChessGraph(nx.DiGraph):
    def add_game(self, game,pos=None,elo=None,name=None):
        #moves = line.move_history
        moves = game.alg_move_history
        fens = game.fen_history
        fens = [' '.join(f.split()[:3]) for f in fens]
        assert len(moves)%2 == 0
        for i in range(0,len(moves),2):
            #full_move = (i+2)/2
            full_move = game.fen_history[i].split()[-1]
            move = '{}.{}..{}'.format(full_move,moves[i],moves[i+1])
            self.add_edge(fens[i],fens[i+2],move=move)
        #self.node[fens[-1]]['pos'] = pos
        self.node[fens[-1]]['elo'] = elo
        self.node[fens[-1]]['name'] = name
        
     
        

def build_graph(lines):
    graph = ChessGraph()
    for line in lines:
        print(line['moves_alg'])
        game = MyGame()
        game.apply_moves(line['moves'])
        graph.add_game(game,line.get('pos'),line.get('elo'),line.get('name'))
        sub_lines = line.get('sub_lines')
        if sub_lines:
            last_fen = game.fen_history[-1]
            for moves in sub_lines:
                game.reset(last_fen)
                game.apply_moves(moves)
                graph.add_game(game)
            
    #graph.node[MyGame.default_fen]['pos'] = [0,0]
        
    return graph

def radial_tree_layout(g,center_node,spoke_angles,radii, sibling_spacing):
    positions = {center_node:(0,0)}
    level_one_nodes = g.successors(center_node)
    for i in range(len(level_one_nodes)):
        angle = spoke_angles[i]
        radius = radii[0]
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius 
        positions[level_one_nodes[i]] = [x,y]
    
    def compute_tree(g,p,node,angle,radius,spacing):
        nodes = g.successors(node)
        if not nodes:
            return [],[]
        arc_angle = (len(nodes)-1)*spacing/radius
        start_angle = angle -  arc_angle/2
        angles = [start_angle + i*spacing/radius for i in range(len(nodes))]
        for i in range(len(nodes)):
            angle = angles[i]
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius 
            p[nodes[i]] = [x,y]
        return nodes,angles
    
    angles = spoke_angles
    nodes = level_one_nodes
    level = 1
    
    while nodes:
        new_nodes = []
        new_angles = []
        for i in range(len(nodes)):
            n,a = compute_tree(g,positions,nodes[i],angles[i],radii[level],sibling_spacing[level-1])
            new_nodes.extend(n)
            new_angles.extend(a)
        level=level+1
        nodes = new_nodes
        angles = new_angles
    
    return positions
            
            



def test():
    
    games = [{'elo':'B50', 'name': 'Sicilian Defense: Modern Variations',
            'moves_alg':'1.e4 c5 2.Nf3 d6',
            'moves': ['e2e4','c7c5','g1f3','d7d6'],
            'sub_lines':[['a2a3','a7a6'],['h2h3','h7h6']]},

            {'elo':'B52', 'name': 'Sicilian Defense: Canal Attack, Main Line',
            'moves_alg':'1.e4 c5 2.Nf3 d6 3.Bb5+ Bd7',
            'moves': ['e2e4','c7c5','g1f3','d7d6','f1b5','b8d7']}
            ]
    
    graph = build_graph(games)
    positions = radial_tree_layout(graph,base_node,[-math.pi/6,0, math.pi/6],
                               [0.15,0.3,0.4,0.5],
                               [0.06,0.03,0.02,0.06])
    labels = {(x[0],x[1]):x[2]['move'] for x in graph.edges(data=True)}
    
    assert graph.nodes(data=True) == [
('rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq', {}),
('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq', {}),
('rnbqkbnr/pp2ppp1/3p3p/2p5/4P3/5N1P/PPPP1PP1/RNBQKB1R w KQkq',{'elo': None, 'name': None}),
('rnbqkbnr/1p2pppp/p2p4/2p5/4P3/P4N2/1PPP1PPP/RNBQKB1R w KQkq',{'elo': None, 'name': None}), 
('rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq',
    {'elo': 'B50', 'name': 'Sicilian Defense: Modern Variations'}),
('r1bqkbnr/pp1npppp/3p4/1Bp5/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq',
       {'elo': 'B52', 'name': 'Sicilian Defense: Canal Attack, Main Line'})]

    assert positions == {
'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq': [0.1299038105676658,
-0.07499999999999998],
'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq': (0, 0),
'rnbqkbnr/pp2ppp1/3p3p/2p5/4P3/5N1P/PPPP1PP1/RNBQKB1R w KQkq': [0.3604222809965292,
  -0.17348135162391087],
'rnbqkbnr/1p2pppp/p2p4/2p5/4P3/P4N2/1PPP1PPP/RNBQKB1R w KQkq': [0.3464101615137755, -0.19999999999999998],
'rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq': [0.2598076211353316, -0.14999999999999997],
'r1bqkbnr/pp1npppp/3p4/1Bp5/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq': [0.3304503980874322, -0.22539417562097205]}
    
    assert labels == {
('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq',
 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq'): '1.e4..c5',
('rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq', 
 'rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq'): '2.Nf3..d6', 
('rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq', 
 'rnbqkbnr/pp2ppp1/3p3p/2p5/4P3/5N1P/PPPP1PP1/RNBQKB1R w KQkq'): '3.h3..h6',
('rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq',
 'r1bqkbnr/pp1npppp/3p4/1Bp5/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq'): '3.Bb5..Nd7',
('rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq', 
 'rnbqkbnr/1p2pppp/p2p4/2p5/4P3/P4N2/1PPP1PPP/RNBQKB1R w KQkq'): '3.a3..a6'}

            
if __name__ == "__main__":
    
    import sys
    
    args = sys.argv[1:]
    
    if args:
        
        with open(args[0]) as f:
            lines = eval(f.read())

        graph = build_graph(lines)


        second = graph.successors(' '.join(Game.default_fen.split()[:3]))

        #third = graph.successors(second[0])
        graph.remove_node(' '.join(Game.default_fen.split()[:3]))

        positions = radial_tree_layout(graph,second[0],[-math.pi/6,0, math.pi/6],
                                       [0.15,0.3,0.4,0.5,0.65,0.80,0.95,1.1,1.25,1.5],
                                       [0.06,0.03,0.02,0.06,0.06,0.03,0.03,0.03,0.03])

        labels = {(x[0],x[1]):x[2]['move'] for x in graph.edges(data=True)}
        nx.draw_networkx(graph,pos=positions,with_labels=False,hold=True,node_size=100)
        nx.draw_networkx_edge_labels(graph,pos=positions,edge_labels=labels,hold=True)
        plt.show()

    else:
        test() 
    
    
    
    
    

        