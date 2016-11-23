
import pdb

import numpy as np

from  dijkstra_algorithm import dijkstra

from datetime import datetime


unit_v = 1.852                   # ship's speed when it sails breaking ice: 1.852km/h
# interaction input
threshold = 1        # threshold of unreachable place
normal_v = 7*unit_v    # ship's normal speed is 7*unit_v
ice_thresh = 0.3       # tell sea between ice fields

class ModisMap(object):
    
    """
        docstring for ModisMap
    """
    
    def __init__(self, prob_mat):

        self.prob_mat = prob_mat        # w*h*3  0:sea, 1:thin ice/cloud, 2:thick ice/cloud
        self.h = prob_mat.shape[0]
        self.w = prob_mat.shape[1]

        
    ############################################################
    #### public methods ########################################
    ############################################################

    # get an path from start to end
    # params:
    #   start   :   (int, int),     matrix subscript of start point
    #   end     :   (int, int)      matrix subscript of destination
    #   ratio   :   float, 0-1      cost = 0.01 + ratio*p(thick/thin ice/cloud) + (1-ratio)*dist
    def getpath(self, start, end, mark, ratio):
        
        assert 0 <= start[0] < self.h
        assert 0 <= start[1] < self.w
        assert 0 <= end[0] < self.h
        assert 0 <= end[1] < self.w
        
        assert isinstance(ratio, float)
        # assert 0 <= ratio <= 1

        start_index = self.__matrixcoor2index(start[0], start[1])
        end_index = self.__matrixcoor2index(end[0], end[1])
        

        #t1 = datetime.now()

        edges = self.__create_edges(start, end, mark, ratio)

        #t2 = datetime.now()

        cost, path = dijkstra(edges, start_index, end_index)

        #t3 = datetime.now()


        #print 'genedges time: %s'%str(t2-t1)    #todo
        #print 'dijkstra time: %s'%str(t3-t2)
        #print 'total time: %s'%str(t3-t1)


        path_points = []
        while path != ():
            node, path = path
            path_points.append(self.__index2matrixcoor(node))

        return cost, path_points



    ############################################################
    #### private methods #######################################
    ############################################################    

    #@profile
    def __create_edges(self, start, end, mark, ratio):

        # generate a retangle search area according to start & end
        # todo : make the retangle close to square
        # todo : make sure search area won't out of bounds
        i_search_range = [0, 0]
        j_search_range = [0, 0]
        i_search_range[0] = min(start[0], end[0]) - 10
        i_search_range[1] = max(start[0], end[0]) + 10
        j_search_range[0] = min(start[1], end[1]) - 10
        j_search_range[1] = max(start[1], end[1]) + 10

        offset = [[0, -1], [-1, -1], [-1, 0], [-1, 1]]
        dist = [1, 1.414, 1, 1.414]

        # generate edges in search area 
        edges = []
        for index in xrange(0, 4):
            if mark == 0:           # cost is time, it equals to 1/(1-prob(sea))
                for i in xrange(i_search_range[0], i_search_range[1]):   # right side +1 ?
                    for j in xrange(j_search_range[0], j_search_range[1]):
                        i2, j2 = i+offset[index][0], j+offset[index][1]
                        if not np.isnan(self.prob_mat[i, j, 0]):
                            if not np.isnan(self.prob_mat[i2, j2, 0]):
                                p1_index = i*self.w + j
                                p2_index = i2*self.w + j2
                                if self.prob_mat[i2, j2, 2] < threshold:     # otherwise, this point is unreachable
                                    cost1 = 0.0
                                    value = np.mean(np.multiply(self.prob_mat[i2-1:i2+2,j2-1:j2+2,1],np.ones([3,3])))
                                    if value < ice_thresh:    # normal speed
                                        cost1 = dist[index] / normal_v               # unit of point is 5km
                                    else:
                                        cost1 = dist[index] / unit_v
                                    edges.append((p1_index, p2_index, cost1))
                                if self.prob_mat[i, j, 2] < threshold:
                                    cost2 = 0.0
                                    value = np.mean(np.multiply(self.prob_mat[i-1:i+2,j-1:j+2,1],np.ones([3,3])))
                                    if value < ice_thresh:    # normal speed
                                        cost2 = dist[index] / normal_v
                                    else:
                                        cost2 = dist[index] / unit_v
                                    edges.append((p2_index, p1_index, cost2))
            elif mark == 1:         # icebreaking and short path
                                    # the cost of (p1-p2) is 0.01 + ratio*(p(thick|p2)) + (1-ratio)*dist
                import math
                cost_common = 0.01
                if ratio <= 1.0:
                    cost_common = math.exp((1.0-ratio)*dist[index]) + cost_common
                else:
                    cost_common = dist[index] + cost_common
                for i in xrange(i_search_range[0], i_search_range[1]):   # right side +1 ?
                    for j in xrange(j_search_range[0], j_search_range[1]):
                        i2, j2 = i+offset[index][0], j+offset[index][1]
                        if not np.isnan(self.prob_mat[i, j, 0]):
                            if not np.isnan(self.prob_mat[i2, j2, 0]):
                                p1_index = i*self.w + j
                                p2_index = i2*self.w + j2
                                if self.prob_mat[i2, j2, 2] < threshold:     # otherwise, this point is unreachable
                                    cost1 = math.exp(ratio*(self.prob_mat[i2, j2, 2])) + cost_common # p1->p2
                                    edges.append((p1_index, p2_index, cost1))
                                if self.prob_mat[i, j, 2] < threshold:
                                    cost2 = math.exp(ratio*(self.prob_mat[i, j, 2])) + cost_common   # p2->p1
                                    edges.append((p2_index, p1_index, cost2))
        return edges


    def __matrixcoor2index(self, i, j):
        
        assert isinstance(i, int) or isinstance(i, long)
        assert isinstance(j, int) or isinstance(j, long)
        assert 0 <= i < self.h
        assert 0 <= j < self.w

        return i*self.w + j

    def __index2matrixcoor(self, index):

        assert isinstance(index, int) or isinstance(index, long)
        assert 0 <= index < self.h*self.w
        
        i = index/self.w
        j = index%self.w
        return i, j

# main for test

if __name__ == '__main__':

    import pickle
    prob_mat = pickle.load(open('data/CURRENT_RASTER_1000.prob', 'rb'))

    model = ModisMap(prob_mat)

    start = (200, 200)
    end = (600, 600)
    ratio = 0.0
    model.getpath(start, end, ratio)