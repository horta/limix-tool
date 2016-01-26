import h5py
import numpy as np
import os
import tempfile
import shutil

def tree(f_or_filepath, root_name='/', ret=False):
    if isinstance(f_or_filepath, str):
        with h5py.File(f_or_filepath, 'r') as f:
            _tree(f, root_name, ret)
    else:
        _tree(f_or_filepath, root_name, ret)

def _tree(f, root_name='/', ret=False):
    import asciitree

    _names = []
    def get_names(name, obj):
        print name, type(obj)
        if isinstance(obj, h5py._hl.dataset.Dataset):
            dtype = str(obj.dtype)
            shape = str(obj.shape)
            _names.append("%s [%s, %s]" % (name, dtype, shape))
        else:
            _names.append(name)

    f.visititems(get_names)
    class Node(object):
        def __init__(self, name, children):
            self.name = name
            self.children = children

        def __str__(self):
            return self.name
    root = Node(root_name, dict())

    def add_to_node(node, ns):
        if len(ns) == 0:
            return
        if ns[0] not in node.children:
            node.children[ns[0]] = Node(ns[0], dict())
        add_to_node(node.children[ns[0]], ns[1:])

    _names = sorted(_names)
    for n in _names:
        ns = n.split('/')
        add_to_node(root, ns)

    def child_iter(node):
        keys = node.children.keys()
        indices = np.argsort(keys)
        indices = np.asarray(indices)
        return list(np.asarray(node.children.values())[indices])

    msg = asciitree.draw_tree(root, child_iter)
    if ret:
        return msg
    print msg

def copy_memmap_h5dt(arr, dt):
    if arr.ndim > 2:
        raise Exception("I don't know how to handle arrays" +
                        " with more than 2 dimensions yet.")
    assert arr.shape == dt.shape
    if arr.ndim == 1:
        dt[:] = arr[:]
    else:
        if dt.chunks is not None:
            chunk_row = dt.chunks[0]
        else:
            chunk_row = 512
        r = 0
        while r < arr.shape[0]:
            re = r + chunk_row
            re = min(re, arr.shape[0])
            dt[r:re,:] = arr[r:re,:]
            r = re

class Memmap(object):
    def __init__(self, filepath, path):
        self._filepath = filepath
        self._path = path
        self._folder = None
        self._X = None

    def __enter__(self):
        self._folder = tempfile.mkdtemp()
        with h5py.File(self._filepath, 'r') as f:
            dt = f[self._path]
            shape = dt.shape
            dtype = dt.dtype
            X = np.memmap(os.path.join(self._folder, 'X'), mode='write',
                          shape=shape, dtype=dtype)
            dt.read_direct(X)
            del X
        X = np.memmap(os.path.join(self._folder, 'X'), mode='r',
                      shape=shape, dtype=dtype)
        self._X = X
        return X
    def __exit__(self, *args):
        del self._X
        shutil.rmtree(self._folder)
