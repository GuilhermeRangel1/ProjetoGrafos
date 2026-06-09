class Grafo:
    def __init__(self, dirigido=False):
        self._adj = {}
        self._nos = []
        self.dirigido = dirigido

    def adicionar_no(self, no):
        if no not in self._adj:
            self._adj[no] = []
            self._nos.append(no)

    def adicionar_aresta(self, u, v, peso=1.0):
        self.adicionar_no(u)
        self.adicionar_no(v)
        self._adj[u].append((v, peso))
        if not self.dirigido:
            self._adj[v].append((u, peso))

    def obter_todos_nos(self):
        return list(self._nos)

    def obter_vizinhos_com_peso(self, u):
        return list(self._adj.get(u, []))

    def obter_vizinhos_simples(self, u):
        return [v for v, _ in self._adj.get(u, [])]

    def obter_todas_arestas(self):
        arestas = []
        for u in self._nos:
            for v, peso in self._adj[u]:
                arestas.append((u, v, peso))
        return arestas
