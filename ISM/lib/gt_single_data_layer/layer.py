# --------------------------------------------------------
# FCN
# Copyright (c) 2016 RSE at UW
# Licensed under The MIT License [see LICENSE for details]
# Written by Yu Xiang
# --------------------------------------------------------

"""The data layer used during training to train a FCN for single frames.
"""

import caffe
from ism.config import cfg
from gt_single_data_layer.minibatch import get_minibatch
import numpy as np
import yaml
from utils.voxelizer import Voxelizer

class GtSingleDataLayer(caffe.Layer):
    """segmentation data layer used for training."""

    def _shuffle_roidb_inds(self):
        """Randomly permute the training roidb."""
        self._perm = np.random.permutation(np.arange(len(self._roidb)))
        self._cur = 0

    def _get_next_minibatch_inds(self):
        """Return the roidb indices for the next minibatch."""
        if self._cur + cfg.TRAIN.IMS_PER_BATCH >= len(self._roidb):
            self._shuffle_roidb_inds()

        db_inds = self._perm[self._cur:self._cur + cfg.TRAIN.IMS_PER_BATCH]
        self._cur += cfg.TRAIN.IMS_PER_BATCH

        return db_inds

    def _get_next_minibatch(self):
        """Return the blobs to be used for the next minibatch."""
        db_inds = self._get_next_minibatch_inds()
        minibatch_db = [self._roidb[i] for i in db_inds]
        return get_minibatch(minibatch_db, self._voxelizer)

    # this function is called in training the net
    def set_roidb(self, roidb):
        """Set the roidb to be used by this layer during training."""
        self._roidb = roidb
        self._shuffle_roidb_inds()

    def setup(self, bottom, top):
        """Setup the GtDataLayer."""

        # parse the layer parameter string, which must be valid YAML
        layer_params = yaml.load(self.param_str)

        self._num_classes = layer_params['num_classes']
        self._voxelizer = Voxelizer(cfg.TRAIN.GRID_SIZE, self._num_classes)

        if cfg.TRAIN.VERTEX_REG:
            self._name_to_top_map = {
                'data_image_color': 0,
                'data_image_depth': 1,
                'data_image_normal': 2,
                'data_label': 3,
                'data_depth': 4,
                'data_meta_data': 5,
                'data_vertex_targets': 6,
                'data_vertex_weights': 7}
        else:
            self._name_to_top_map = {
                'data_image_color': 0,
                'data_image_depth': 1,
                'data_image_normal': 2,
                'data_label': 3,
                'data_depth': 4,
                'data_meta_data': 5}

        # data blob: holds a batch of N images, each with 3 channels
        # The height and width (256 x 256) are dummy values
        top[0].reshape(1, 3, 480, 640)
        top[1].reshape(1, 3, 480, 640)
        top[2].reshape(1, 3, 480, 640)
        top[3].reshape(1, 1, 480, 640)
        top[4].reshape(1, 1, 480, 640)
        top[5].reshape(1, 48, 1, 1)
        if cfg.TRAIN.VERTEX_REG:
            top[6].reshape(1, 3, 480, 640)
            top[7].reshape(1, 3, 480, 640)
            
    def forward(self, bottom, top):
        """Get blobs and copy them into this layer's top blob vector."""
        blobs = self._get_next_minibatch()

        for blob_name, blob in blobs.iteritems():
            top_ind = self._name_to_top_map[blob_name]
            # Reshape net's input blobs
            top[top_ind].reshape(*(blob.shape))
            # Copy data into net's input blobs
            top[top_ind].data[...] = blob.astype(np.float32, copy=False)

    def backward(self, top, propagate_down, bottom):
        """This layer does not propagate gradients."""
        pass

    def reshape(self, bottom, top):
        """Reshaping happens during the call to forward."""
        pass
