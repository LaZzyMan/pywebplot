from pywebplot import *
from palettable.cartocolors.qualitative import Antique_10, Bold_10, Pastel_10, Prism_10, Safe_10, Vivid_10
from GeoMultiGraph import *
from palettable.colorbrewer.sequential import Reds_9, GnBu_9, BuPu_9, Blues_9


if __name__ == '__main__':
    # WEB_SERVER.run()
    mkdir()
    gmg = GeoMultiGraph()
    gmg.load('../src/data/GeoMultiGraph_week', network_list=['2012', '2013', '2014', '2015', '2016', '2017'], generate_nx=True)
    cll = gmg.community_detection_louvain(resolution=1., min_size=10)
    gmg.draw_multi_scale_community(community=cll, cmap=Prism_10, inline=True, title='louvain')
    scll = gmg.community_detection_twice(cll, method='louvain', min_size=10)
    gmg.draw_multi_scale_community(community=scll, cmap=Prism_10, inline=True, title='s-louvain')
    # c_u = gmg.read_multi_tensor_result(filename='K10_result.dat', vec='u')
    # c_v = gmg.read_multi_tensor_result(filename='K10_result.dat', vec='v')
    # view = PlotView(column_num=2, row_num=1, title='multi-tensor')
    # view[0].name = 'u'
    # view[1].name = 'v'
    # maps = [MapBox(name='map_%d' % i,
    #                pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
    #                lon=116.37363,
    #                lat=39.915606,
    #                style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
    #                pitch=55,
    #                bearing=0,
    #                zoom=12,
    #                viewport=view[i]) for i in range(2)]
    # gmg.draw_choropleth_map(map_view=maps[0], data=c_u, value='community',
    #                              title='ucommunity', cmap=Vivid_10)
    # gmg.draw_choropleth_map(map_view=maps[1], data=c_v, value='community',
    #                         title='vcommunity', cmap=Vivid_10)
    # view.plot(inline=True)
    # cl = gmg.community_detection_infomap(min_size=10)
    # gmg.draw_multi_scale_community(community=cl, cmap=Prism_10, inline=True, title='infomap')
    # scl = gmg.community_detection_twice(cl, method='infomap', min_size=10)
    # gmg.draw_multi_scale_community(community=scl, cmap=Prism_10, inline=True, title='s-infomap')
    # cll = gmg.community_detection_louvain(resolution=1., min_size=10)
    # gmg.draw_multi_scale_community(community=cll, cmap=Prism_10, inline=True, title='louvain')
    # scll = gmg.community_detection_twice(cll, method='louvain', min_size=10)
    # gmg.draw_multi_scale_community(community=scll, cmap=Prism_10, inline=True, title='s-louvain')
    # mc = gmg.community_detection_multi_infomap(geo_weight='kde', connect='memory', only_self_transition=True)
    # gmg.draw_multi_scale_community(community=mc, cmap=Pastel_10, inline=True, title='memory-kde-gc')
    # gmg.export(type='MultiTensor', filename='adj.dat')
    # gc = gmg.local_community_detection_infomap(geo_weight='kde', min_size=10)
    # plt = PlotView(column_num=1, row_num=1, title='gc-kde')
    # plt[0].name = 'gc'
    # map = MapBox(name='map_gc',
    #              pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
    #              lon=116.37363,
    #              lat=39.915606,
    #              style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
    #              pitch=55,
    #              bearing=0,
    #              zoom=12,
    #              viewport=plt[0])
    # gmg.draw_choropleth_map(map_view=map, data=gc, value='community', title='gc-kde', cmap=Antique_10)
    # plt.plot(inline=True)
    # connect_dict = ['flow', 'memory', 'all_connect', 'none']
    # geo_weight_dict = ['queen', 'queen2', 'knn', 'kde', 'none']
    # for con in connect_dict:
    #     for geo in geo_weight_dict:
    #         mc = gmg.community_detection_multi_infomap(geo_weight=geo, connect=con, only_self_transition=False)
    #         gmg.draw_multi_scale_community(community=mc, cmap=Pastel_10, inline=True, title='%s-%s' % (con, geo))
    #         plt = PlotView(column_num=1, row_num=1, title='extrusion-%s-%s' % (con, geo))
    #         plt[0].name = '%s-%s' % (con, geo)
    #         map = MapBox(name='map_infomap',
    #                      pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
    #                      lon=116.37363,
    #                      lat=39.915606,
    #                      style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
    #                      pitch=55,
    #                      bearing=0,
    #                      zoom=12,
    #                      viewport=plt[0])
    #         gmg.draw_taz(map_view=map)
    #         gmg.draw_multi_community_extrusion(map_view=map,
    #                                            communities=mc,
    #                                            cmap=Pastel_10,
    #                                            title='%s%s' % (con, geo))
    #         plt.plot(inline=True)
    # closeness_centrality = get_closeness_centrality(gmg.nx_graph[0])
    # plt = PlotView(column_num=1, row_num=1, title='Statistics-Information')
    # plt[0].name = 'closeness_centrality'
    # map = MapBox(name='map_si_0',
    #              pk='pk.eyJ1IjoiaGlkZWlubWUiLCJhIjoiY2o4MXB3eWpvNnEzZzJ3cnI4Z3hzZjFzdSJ9.FIWmaUbuuwT2Jl3OcBx1aQ',
    #              lon=116.37363,
    #              lat=39.915606,
    #              style='mapbox://styles/hideinme/cjtgp37qv0kjj1fup07b9lf87',
    #              pitch=55,
    #              bearing=0,
    #              zoom=12,
    #              viewport=plt[0])
    # gmg.draw_choropleth_map(map_view=map, data=closeness_centrality, value='closeness_centrality',
    #                         title='closeness-centrality', cmap=Reds_9)
    # plt.plot(inline=False)
    # gmg.threshold(t_min=20, generate_nx=True)
    # gmg.transform(func='sqrt', generate_nx=True)
    # gmg.draw_dist(hist=True, kde=False, rug=False, bins=20)
    # gmg.draw_qq_plot()
    # gmg.draw_network(color='white', width=1., value='weight', bk=True, inline=False, row=3, column=2)
