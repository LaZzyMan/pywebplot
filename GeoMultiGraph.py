import numpy as np
import geopandas as gpd
from community import best_partition, modularity
import seaborn as sns
import networkx as nx
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from pywebplot import *
from palettable.colorbrewer.diverging import Spectral_10
from scipy import stats

NETWORK_LIST = ['2012',
                '2013',
                '2014',
                '2015',
                '2016',
                '2017']


class GeoMultiGraph:
    def __init__(self, geo_mapping=None, graph=None):
        self._geo_mapping = geo_mapping
        self._root_graph = graph
        self._graph = graph
        if graph is None:
            self._num_nodes = 0
            self._num_graph = 0
        else:
            self._num_nodes = len(graph[0])
            self._num_graph = len(graph)
        self._nx_graph = None

    def save(self, file_name):
        self._geo_mapping.to_file('src/data/' + file_name + '.geojson', driver='GeoJSON')
        np.save('src/data/' + file_name + '.npy', self._graph)

    def load(self, file_name, generate_nx=False):
        self._graph = np.load('src/data/' + file_name + '.npy')
        self._geo_mapping = gpd.read_file('src/data/' + file_name + '.geojson')
        self._num_nodes = len(self._graph[0])
        self._num_graph = len(self._graph)
        if generate_nx:
            self.__update_nx_graph()

    def recovery(self):
        '''
        recovery the origin data
        :return:
        '''
        self._graph = self._root_graph
        self.__update_nx_graph()

    @property
    def nx_graph(self):
        return self._nx_graph

    @property
    def num_nodes(self):
        return self._num_nodes

    @property
    def num_graph(self):
        return self._num_graph

    @property
    def edges(self):
        print('Generating Edges Data Frame...')
        connect_table = {'from_tazid': [],
                         'to_taziid': [],
                         'weight': [],
                         'network': []}
        for g, index in zip(self.nx_graph, range(self.num_graph)):
            for i in range(self.num_nodes):
                for j in range(self.num_nodes):
                    try:
                        weight = g.adj[i][j]['weight']
                        if weight == 0:
                            continue
                        connect_table['network'].append(NETWORK_LIST[index])
                        connect_table['weight'].append(weight)
                        from_tazid = g.nodes[i]['tazid']
                        to_tazid = g.nodes[j]['tazid']
                        connect_table['to_taziid'].append(to_tazid)
                        connect_table['from_tazid'].append(from_tazid)
                    except KeyError as _:
                        continue
        connect_df = pd.DataFrame.from_dict(connect_table)
        print('Finished.')
        return connect_df

    @property
    def edges_geo(self):
        print('Generating Geo Edges Data Frame...')
        connect_table = {'from_tazid': [],
                         'to_taziid': [],
                         'weight': [],
                         'network': [],
                         'geometry': []}
        for g, index in zip(self.nx_graph, range(self.num_graph)):
            for i in range(self.num_nodes):
                for j in range(self.num_nodes):
                    try:
                        weight = g.adj[i][j]['weight']
                        if weight == 0:
                            continue
                        connect_table['network'].append(NETWORK_LIST[index])
                        connect_table['weight'].append(weight)
                        from_tazid = g.nodes[i]['tazid']
                        to_tazid = g.nodes[j]['tazid']
                        connect_table['to_taziid'].append(to_tazid)
                        connect_table['from_tazid'].append(from_tazid)
                        from_point = self._geo_mapping[self._geo_mapping.tazid == from_tazid].geometry[i].centroid
                        to_point = self._geo_mapping[self._geo_mapping.tazid == to_tazid].geometry[j].centroid
                        connect_table['geometry'].append(LineString([from_point, to_point]))
                    except KeyError as _:
                        continue
            connect_df = gpd.GeoDataFrame.from_dict(connect_table)
            print('Finished.')
            return connect_df

    def transform(self, func='log', generate_nx=False):
        '''
        call func for weight of the graph
        :param func:
        :param generate_nx:
        :return:
        '''
        def tf_ln(x):
            if x == 0:
                return 0
            else:
                return np.log(x)

        def tf_log2(x):
            if x == 0:
                return 0
            else:
                return np.log2(x)

        def tf_log10(x):
            if x == 0:
                return 0
            else:
                return np.log10(x)

        def tf_sqrt(x):
            return np.sqrt(x)
        func_dict = {
            'log': tf_ln,
            'log2': tf_log2,
            'log10': tf_log10,
            'sqrt': tf_sqrt
        }
        if func in func_dict.keys():
            self._graph = np.vectorize(func_dict[func])(self._graph)
        if func == 'cox':
            expand = [stats.boxcox(g.reshape((self.num_nodes * self.num_nodes, )) + 0.00001)[0] for g in self._graph]
            self._graph = np.array([g.reshape(self.num_nodes, self.num_nodes) for g in expand])
        if generate_nx:
            self.__update_nx_graph()

    def threshold(self, t_min=0, t_max=1000000, generate_nx=False):
        '''
        weight bigger than y_max will be set to t_max, lower than t_min will be set to 0.
        :param t_min:
        :param t_max:
        :param generate_nx:
        :return:
        '''
        def process(x):
            if x < t_min:
                return 0
            if x > t_max:
                return t_max
            return x

        self._graph = np.vectorize(process)(self._graph)
        if generate_nx:
            self.__update_nx_graph()

    def community_detection_louvain(self, resolution=1., min_size=10):
        def louvain(g):
            table = {
                'tazid': [],
                'community': []
            }
            print('Louvain for network %s...' % g.graph['date'])
            g = nx.Graph(g)
            p = best_partition(g, weight='weight', resolution=resolution)
            print('Network %s Modularity: %f.' % (g.graph['date'], modularity(p, g, weight='weight')))
            for key, item in p.items():
                table['tazid'].append(self.__get_tazid(key))
                table['community'].append(item)
            print('Finished %s.' % g.graph['date'])
            return pd.DataFrame.from_dict(table)
        df_partiton = map(louvain, self.nx_graph)
        return self.__simplify_community(list(df_partiton), size=min_size)

    @property
    def closeness_centrality(self):
        table = {'tazid': [],
                 'closeness_centrality': []}
        closeness_centrality = []
        for g in self.nx_graph:
            print('Closeness Centrality for %s...' % g.graph['date'])
            cc = nx.closeness_centrality(g)
            for k, i in cc.items():
                table['tazid'].append(g.nodes[k]['tazid'])
                table['closeness_centrality'].append(i)
            closeness_centrality.append(pd.DataFrame.from_dict(table))
            table['tazid'].clear()
            table['closeness_centrality'].clear()
        print('Finished.')
        return closeness_centrality

    @property
    def degree(self):
        table = {'tazid': [],
                 'in_degree': []}
        degree = []
        for g in self.nx_graph:
            print('Degree for %s...' % g.graph['date'])
            for k in range(self.num_nodes):
                table['tazid'].append(g.nodes[k]['tazid'])
                table['degree'].append(g.degree(k, weight='weight'))
            degree.append(pd.DataFrame.from_dict(table))
            table['tazid'].clear()
            table['degree'].clear()
        print('Finished.')
        return degree

    @property
    def in_degree(self):
        table = {'tazid': [],
                 'in_degree': []}
        in_degree = []
        for g in self.nx_graph:
            print('In Degree for %s...' % g.graph['date'])
            for k in range(self.num_nodes):
                table['tazid'].append(g.nodes[k]['tazid'])
                table['in_degree'].append(g.in_degree(k, weight='weight'))
            in_degree.append(pd.DataFrame.from_dict(table))
            table['tazid'].clear()
            table['in_degree'].clear()
        print('Finished.')
        return in_degree

    @property
    def out_degree(self):
        table = {'tazid': [],
                'out_degree': []}
        out_degree = []
        for g in self.nx_graph:
            print('Out Degree for %s...' % g.graph['date'])
            for k in range(self.num_nodes):
                table['tazid'].append(g.nodes[k]['tazid'])
                table['out_degree'].append(g.out_degree(k, weight='weight'))
            out_degree.append(pd.DataFrame.from_dict(table))
            table['tazid'].clear()
            table['out_degree'].clear()
        print('Finished.')
        return out_degree

    def draw_dist(self, hist=True, kde=True, rug=True, bins=10):
        sns.set_style('ticks')
        sns.set(color_codes=True)
        graphs = sns.FacetGrid(self.edges, col='network')
        graphs.map(sns.distplot, 'weight', hist=hist, kde=kde, rug=rug, bins=bins)
        plt.show()

    def draw_qq_plot(self):
        def qqplot(x, **kwargs):
            stats.probplot(x, dist='norm', plot=plt, fit=False)

        sns.set_style('ticks')
        sns.set(color_codes=True)
        graphs = sns.FacetGrid(self.edges, col='network')
        graphs.map(qqplot, 'weight')
        plt.show()

    def draw_choropleth_map(self, map_view, data, value='', title='Choropleth Map', cmap=Spectral_10):
        value_min = data[value].min()
        value_max = data[value].max()

        def set_color(x):
            mpl_colormap = cmap.get_mpl_colormap(N=value_max-value_min)
            rgba = mpl_colormap(x[value] + value_min)
            return rgb2hex(rgba[0], rgba[1], rgba[2])
        value_geo_map = self._geo_mapping.merge(data, on='tazid')
        value_geo_map = value_geo_map[['tazid', value, 'geometry']]
        value_geo_map['color'] = value_geo_map.apply(set_color, axis=1)
        value_geo_map.to_file('src/data/%s.geojson' % title, driver='GeoJSON')
        source = GeojsonSource(id=value, data='data/%s.geojson' % title)
        map_view.add_source(source)
        layer = FillLayer(id=value, source=value, p_fill_opacity=0.7, p_fill_color=['get', 'color'])
        map_view.add_layer(layer)
        map_view.update()

    def draw_multi_scale_community(self, community, cmap=Spectral_10):
        view = PlotView(column_num=3, row_num=2, title='Geo-Multi-Graph')
        for subview, i in zip(view, range(self.num_graph)):
            subview.name = NETWORK_LIST[i]
        maps = [MapBox(name='map_%d' % i,
                       pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
                       lon=116.37363,
                       lat=39.915606,
                       style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
                       pitch=55,
                       bearing=0,
                       zoom=12,
                       viewport=view[i]) for i in range(self.num_graph)]
        for i in range(self.num_graph):
            self.draw_choropleth_map(map_view=maps[i], data=community[i], value='community', title='%scommunity' % NETWORK_LIST[i], cmap=cmap)
        view.plot()

    def draw_single_network(self, map_view, network=NETWORK_LIST[0], color='white', width=1., value='weight', title='network', bk=True):
        connect_df = self.edges_geo[self.edges_geo['network'] == network]
        min_weight = connect_df['weight'].min()
        max_weight = connect_df['weight'].max()
        connect_df['opacity'] = connect_df['weight'].map(
            lambda x: (x - min_weight) / (max_weight - min_weight) * 0.8 + 0.00)
        draw_df = connect_df[['geometry', 'opacity']]
        draw_df.to_file('src/data/%s.geojson' % title, driver='GeoJSON')
        network_source = GeojsonSource(id=value, data='data/%s.geojson' % title)
        map_view.add_source(network_source)
        bk_layer = BackgroundLayer(id='bk',
                                   p_background_opacity=0.7,
                                   p_background_color='#000000')
        network_layer = LineLayer(id=title,
                                  source=title,
                                  p_line_color=color,
                                  p_line_width=width,
                                  p_line_opacity=['get', 'opacity'])
        if bk:
            map_view.add_layer(bk_layer)
        map_view.add_layer(network_layer)
        map_view.update()

    def draw_taz(self, map_view, color='#3BA1C3', fill_opacity=0.3):
        taz_unit_df = self._geo_mapping['geometry']
        taz_unit_df.to_file('src/data/taz.geojson', driver='GeoJSON')
        source = GeojsonSource(id='taz', data='data/taz.geojson')
        map_view.add_source(source)
        layer = FillLayer(id='taz', source='taz', p_fill_opacity=fill_opacity, p_fill_color=color)
        map_view.add_layer(layer)
        map_view.update()

    def __get_tazid(self, index):
        return self._geo_mapping['tazid'][index]

    def __update_nx_graph(self):
        G = []
        for l, time in zip(self._graph, NETWORK_LIST):
            print('Generating Network %s' % time)
            g = nx.DiGraph(date=time)
            for i in range(len(l)):
                g.add_node(i, tazid=self.__get_tazid(i))
            for i in range(len(l)):
                for j in range(len(l)):
                    if i == j:
                        continue
                    g.add_edge(i, j, weight=l[i, j])
            G.append(g)
        self._nx_graph = G

    def simplify_community(self, data, size=10):
        df_s_community = []
        for community in data:
            c_list = {}
            r_list = []
            un_list = []
            for _, line in community.iterrows():
                if line['community'] in c_list.keys():
                    c_list[line['community']].append(line['tazid'])
                else:
                    c_list[line['community']] = [line['tazid']]
            for key, item in c_list.items():
                if len(item) <= size:
                    for i in item:
                        un_list.append(i)
                else:
                    r_list.append(item)
            r_list.append(un_list)
            table = {
                'tazid': [],
                'community': []
            }
            for r, i in zip(r_list, range(len(r_list))):
                for k in r:
                    table['tazid'].append(k)
                    table['community'].append(i)
            df_s_community.append(pd.DataFrame.from_dict(table))
        return df_s_community


if __name__ == '__main__':
    gmg = GeoMultiGraph()
    gmg.load('GeoMultiGraph_week')
    # gmg.threshold(t_min=3, generate_nx=True)
    # gmg.transform(func='sqrt', generate_nx=True)
    # gmg.draw_dist(hist=True, kde=False, rug=False, bins=20)
    # gmg.draw_qq_plot()
    # cl = gmg.community_detection_louvain(min_size=20)
    cl = []
    for i in NETWORK_LIST:
        cl.append(pd.read_csv('%s.csv' % i))
    cl = gmg.simplify_community(data=cl, size=20)
    gmg.draw_multi_scale_community(community=cl, cmap=Spectral_10)
    '''
    cc = gmg.closeness_centrality
    in_degree = gmg.in_degree
    out_degree = gmg.out_degree
    degree = gmg.degree
    plt = PlotView(column_num=2, row_num=2, title='Geo-Multi-Graph')
    plt[0, 0].name = 'Closeness-Centrality'
    plt[1, 0].name = 'in-degree'
    plt[1, 1].name = 'out-degree'
    plt[0, 1].name = 'degree'
    mb_0 = MapBox(name='map-0',
                  pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
                  lon=116.37363,
                  lat=39.915606,
                  style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
                  pitch=55,
                  bearing=0,
                  zoom=12,
                  viewport=plt[0, 0])
    mb_1 = MapBox(name='map-1',
                  pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
                  lon=116.37363,
                  lat=39.915606,
                  style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
                  pitch=55,
                  bearing=0,
                  zoom=12,
                  viewport=plt[1, 0])
    mb_2 = MapBox(name='map-2',
                  pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
                  lon=116.37363,
                  lat=39.915606,
                  style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
                  pitch=55,
                  bearing=0,
                  zoom=12,
                  viewport=plt[1, 1])
    mb_3 = MapBox(name='map-3',
                  pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
                  lon=116.37363,
                  lat=39.915606,
                  style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
                  pitch=55,
                  bearing=0,
                  zoom=12,
                  viewport=plt[0, 1])
    gmg.draw_choropleth_map(map_view=mb_0, data=cc[0], value='closeness_centrality', title='cc')
    gmg.draw_choropleth_map(map_view=mb_1, data=in_degree[0], value='in_degree', title='in')
    gmg.draw_choropleth_map(map_view=mb_2, data=out_degree[0], value='out_degree', title='out')
    gmg.draw_single_network(map_view=mb_3, network='2012')
    '''
