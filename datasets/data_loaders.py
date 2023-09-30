import os
import numpy as np
import torch
from torch.utils.data import DataLoader

from .general_eval import MVSDataset
from .blended_dataset import BlendedMVSDataset
from .dtu_yao import DTUMVSDataset

np.random.seed(1234)


class DTULoader(DataLoader):

    def __init__(self, data_path, data_list, mode, num_srcs, num_depths, interval_scale=1.0,
                 shuffle=True, seq_size=49, batch_size=1, fix_res=False, max_h=None, max_w=None,
                 dataset_eval='dtu', refine=True):
        if (mode == 'train') or (mode == 'val'):
            self.mvs_dataset = DTUMVSDataset(data_path, data_list, mode, num_srcs, num_depths, interval_scale,
                                             shuffle=shuffle, seq_size=seq_size, batch_size=batch_size)
        else:
            self.mvs_dataset = MVSDataset(data_path, data_list, mode, num_srcs, num_depths, interval_scale,
                                          shuffle=shuffle, seq_size=seq_size, batch_size=batch_size,
                                          max_h=max_h, max_w=max_w, fix_res=fix_res, dataset=dataset_eval, refine=refine)
        drop_last = True if mode == 'train' else False
        super().__init__(self.mvs_dataset, batch_size=batch_size, shuffle=shuffle,
                         num_workers=4, pin_memory=True, drop_last=drop_last)

        self.n_samples = len(self.mvs_dataset)

    def get_num_samples(self):
        return len(self.mvs_dataset)


class BlendedLoader(DataLoader):

    def __init__(self, data_path, data_list, mode, num_srcs, num_depths, interval_scale=1.0,
                 shuffle=True, seq_size=49, batch_size=1, fix_res=False, max_h=None, max_w=None):
        if (mode == 'train') or (mode == 'val'):
            self.mvs_dataset = BlendedMVSDataset(data_path, data_list, mode, num_srcs, num_depths, interval_scale,
                                                 shuffle=shuffle, seq_size=seq_size, batch_size=batch_size)
        else:
            self.mvs_dataset = MVSDataset(data_path, data_list, mode, num_srcs, num_depths, interval_scale,
                                          shuffle=shuffle, seq_size=seq_size, batch_size=batch_size,
                                          max_h=max_h, max_w=max_w, fix_res=fix_res, dataset='dtu')
        drop_last = True if mode == 'train' else False
        super().__init__(self.mvs_dataset, batch_size=batch_size, shuffle=shuffle,
                         num_workers=4, pin_memory=True, drop_last=drop_last)

        self.n_samples = len(self.mvs_dataset)

    def get_num_samples(self):
        return len(self.mvs_dataset)


if __name__ == '__main__':
    from utils import tocuda
    import MYTH
    import matplotlib.pyplot as plt

    data_loader = DTULoader('/home/khangtg/Documents/lab/mvs/dataset/mvs/dtu_dataset/train',
                            '/home/khangtg/Documents/lab/depth-fusion/lists/dtu/subsub_train.txt',
                            'train', 5, 192, 1.06, batch_size=2)
    for idx, sample in enumerate(data_loader):
        sample_cuda = tocuda(sample)
        depths, imgs = sample_cuda["input_depths"], sample_cuda["imgs"]
        proj_matrices = sample_cuda["proj_matrices"]["stage3"]
        intrinsics, extrinsics = proj_matrices[:, :, 1, :, :], proj_matrices[:, :, 0, :, :]
        camera_params = torch.matmul(intrinsics[..., :3, :3], extrinsics[..., :3, :4])
        warped_depths, warped_imgs, _ = MYTH.DepthColorAngleReprojectionNeighbours.apply(depths, imgs,
                                                                                          camera_params, 1.0)
        ref_img = warped_imgs[0, 0, ...]

        ref_img = ref_img.permute(1, 2, 0)
        ref_img = ref_img.cpu().numpy()

        fig = plt.figure(figsize=(20, 20))
        ax1 = fig.add_subplot(3, 2, 1)
        plt.imshow(ref_img)

        for i in range(1, warped_imgs.size(1)):
            src_img = warped_imgs[0, i, ...]
            src_img = src_img.permute(1, 2, 0)
            src_img = src_img.cpu().numpy()
            axi = fig.add_subplot(3, 2, i+1)
            plt.imshow(src_img)
        plt.show()


