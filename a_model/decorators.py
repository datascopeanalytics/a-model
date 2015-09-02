from functools import wraps
import cPickle as pickle
import os
import time
import md5

from . import utils


def run_or_cache(method):
    """This decorator is useful for caching results from random trials to keep
    results consistent from script to script. This stores the result on disk
    and keeps it in memory after it is read from disk.
    """

    # TODO: cache results based on when "today" actually is

    # this is a global cache that avoids re-reading data from disk when its
    # already been read from disk
    _cache = {}

    @wraps(method)
    def wrapped_method(self, *args, **kwargs):

        # use the method and call signature to cache the result in memory
        m = md5.new()
        for arg in args:
            m.update(str(arg))
        for k, v in sorted(kwargs.iteritems()):
            m.update(str(k))
            m.update(str(v))
        cache_key = method.func_name + '-' + m.hexdigest()

        # cache result in memory to avoid rereading from disk
        if cache_key in _cache:
            return _cache[cache_key]

        # load the data from cache, if possible
        cache_filename = os.path.join(
            utils.DATA_ROOT, cache_key + '.pkl',
        )
        result = None
        if os.path.exists(cache_filename):
            age = time.time() - os.path.getmtime(cache_filename)
            if age < utils.MAX_CACHE_AGE:
                with open(cache_filename) as stream:
                    result = pickle.load(stream)

        # otherwise, run the method and cache the result
        if result is None:
            result = method(self, *args, **kwargs)
            with open(cache_filename, 'w') as stream:
                pickle.dump(result, stream)

        # remember this result in memory to avoid re-running or reading from
        # disk again
        _cache[cache_key] = result
        return result

    return wrapped_method
