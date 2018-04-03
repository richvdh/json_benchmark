#!/usr/bin/env python
from __future__ import print_function
import importlib
import json
import timeit
from collections import OrderedDict

# number of runs over the data for each repeat
N_RUNS = 20

# number of times to repeat the runs. We'll take the fastest run.
N_REPEATS = 5

# modules to benchmark. 'simplejson_static' uses a static JSONEncoder/Decoder.
#
# MODULES = ('json', 'simplejson_static', 'simplejson')
MODULES = ('json', 'simplejson_static')

DUMP_KWARGS = {
    'simplejson': {'namedtuple_as_object': False, },
    'simplejson_static': {'namedtuple_as_object': False, },
}

def benchmark_loads(module, data):
    module['loads'](data)


def benchmark_dumps(module, obj):
    module['dumps'](obj)


def benchmark_loads_byline(module, lines):
    for line in lines:
        module['loads'](line)


def benchmark_dumps_byline(module, lines):
    for obj in lines:
        module['dumps'](obj)


def import_mod(name):

    kwargs = DUMP_KWARGS.get(name, {})
    result = {}
    if name == 'simplejson_static':
        mod = importlib.import_module('simplejson')
        enc = mod.JSONEncoder(**kwargs)
        dec = mod.JSONDecoder()
        result['dumps'] = enc.encode
        result['loads'] = dec.decode
        result['version'] = mod.__version__
        return result

    mod = importlib.import_module(name)
    result['version'] = mod.__version__
    if name == 'canonicaljson':
        result['dumps'] = mod.encode_canonical_json
    else:
        d0 = mod.dumps
        result['loads'] = mod.loads
        result['dumps'] = lambda o: d0(o, **kwargs)
    return result


def import_modules():
    for name in MODULES:
        try:
            yield name, import_mod(name)
        except ImportError:
            print('Unable to import {}'.format(name))


def print_results(results):
    benchmarks = list(results)

    print (" "*25, *("%20s" % b for b in benchmarks))

    modules = OrderedDict(((m, None) for b in results.values() for m in b.keys()))
    for module_name in modules:
        print(
            "%-25s" % module_name,
            *("%20f" % results[benchmark_name].get(module_name, 0)
                for benchmark_name in benchmarks)
        )


def run_benchmarks():
    with open('data/large.json') as f:
        large_obj_data = f.read()
    large_obj = json.loads(large_obj_data)

    with open('data/one-json-per-line.txt') as f:
        small_objs_data = f.readlines()
    small_objs = [json.loads(line) for line in small_objs_data]

    load_benchmarks = [
        ('loads (large obj)', lambda m: benchmark_loads(m, large_obj_data)),
        ('loads (small objs)', lambda m: benchmark_loads_byline(m, small_objs_data)),
    ]

    dump_benchmarks = [
        ('dumps (large obj)', lambda m: benchmark_dumps(m, large_obj)),
        ('dumps (small objs)', lambda m: benchmark_dumps_byline(m, small_objs)),
    ]

    results = OrderedDict()
    modules = import_modules()
    for module_name, mod in modules:
        module_name = "%s %s" % (module_name, mod['version'])
        print('Running {} benchmarks...'.format(module_name))
        benchmarks = []
        if 'loads' in mod:
            benchmarks += load_benchmarks
        if 'dumps' in mod:
            benchmarks += dump_benchmarks

        for benchmark_name, fn in benchmarks:
            print('   %s...' % benchmark_name)
            time = timeit.timeit(lambda: fn(mod), number=1)
            print('      first run: %f' % time)
            #results.setdefault(benchmark_name+"1", OrderedDict())
            #results[benchmark_name+"1"][module_name] = time

            times = timeit.repeat(lambda: fn(mod), number=N_RUNS, repeat=N_REPEATS)
            best = min(times)
            print('      %i loops, best of %i: %f sec per loop' % (
                N_RUNS, len(times), best/N_RUNS,
            ))

            results.setdefault(benchmark_name, OrderedDict())
            results[benchmark_name][module_name] = best/N_RUNS

    print('\nResults\n=======')
    print_results(results)

if __name__ == '__main__':
    run_benchmarks()
