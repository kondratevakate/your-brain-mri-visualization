#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""Parses FreeSurfer statistics then flattens included table of brain structure features into 1-row table as DataFrame.

::Input:: ``sub-ID/stats/aseg.stats`` | ``sub-ID/stats/rh.aparc.stats`` | ``sub-ID/stats/lh.aparc.stats``
::Output:: ``morphometry.csv``

.. Examples::

    Default using (being in the subject directory yielded from FreeSurfer)::

        $ python flattener.py

    CLI using::

        $ python flattener.py -s sub-ID -i stats/aseg.stats stats/rh.aparc.stats stats/lh.aparc.stats -o morphometry.csv

    As module::

        >>> import pandas as pd
        >>> from flattener import flatten_freesurfer_stats as ffss
        >>> stats = ['sub-ID/stats/aseg.stats', 'sub-ID/stats/rh.aparc.stats', 'sub-ID/stats/lh.aparc.stats']
        >>> df = pd.DataFrame()
        >>> for path in stats:
        >>>     df = pd.concat([df, ffss(path)], axis = 1)
        >>> df.to_csv('sub-ID/derivatives/morphometry.csv')
        
        Written by Arseny Bozhenko, mind copywriting.
"""

import warnings
warnings.filterwarnings("ignore")


def flatten_freesurfer_stats(path):
    """
        Parses FreeSurfer statistics then flattens included table of brain structure features into 1-row table as DataFrame.
    """

    from os.path import basename
    import pandas as pd
    from plumbum.colors import fatal

    try:
        # Get line with column names from file of FreeSurfer statistics.
        ColHeader = next(filter(lambda line: line.startswith('# ColHeaders'), open(path).readlines()))
        # Ignore first '#', 'ColHeaders'. Leave column names only.
        names = ColHeader.split()[2:]

        data = pd.read_csv(path, names=names, comment='#', delim_whitespace=True, dtype=str)
        columns = [col for col in filter(
            lambda column: column not in ['Index', 'SegId', 'StructName'],
            data.columns
        )]
        StructNames = data['StructName']
        data = pd.DataFrame(data[columns].T.values.flatten()).T

        # Get prefix (e.g. 'rh') from file name like ``rh.aparc.stats``
        # as suffix for names of 1-row columns had been flattened from DataFrame.
        filename = basename(path).split('.')
        suffix = [filename[0]] if len(filename) > 2 else [] # There is no prefix from file name like ``aseg.stats``
        data.columns = ['_'.join([prefix, infix] + suffix) for infix in columns for prefix in StructNames]
        return data
    except StopIteration:
        print(fatal | "There is no header with column names starting with ColHeaders in the file", path)
    except FileNotFoundError as e:
        print(fatal | str(e))
    except KeyError as e:
        print(fatal | "There is no column", str(e))
    return pd.DataFrame()


if __name__ == '__main__':
    import argparse
    from shlex import quote
    import os.path
    import pandas as pd

    parser = argparse.ArgumentParser(
        description='Parses FreeSurfer statistics then flattens included table(s) of brain structure features into 1-row table as CSV.',
        usage='python flattener.py -s sub-ID/stats -i aseg.stats rh.aparc.stats lh.aparc.stats -o morphometry.csv'
    )

    group = parser.add_argument_group('Input/output pathes')

    group.add_argument('-i', '--input', help='Input pathes to .stats files yielded from FreeSurfer',
                       nargs='*', required=False, default=['stats/aseg.stats', 'stats/rh.aparc.stats', 'stats/lh.aparc.stats'])

    group.add_argument('-s', '--subject', help='Input path to subject directory yielded from FreeSurfer',
                       required=False, default=os.getcwd())

    group.add_argument('-o', '--output', help='Output filename [default: morphometry.csv within current directory]',
                       required=False, default=os.path.join(os.getcwd(), 'morphometry.csv'))

    parser.add_argument('-q', '--quiet', help='Don`t print the output filename', required=False, action='store_true')
    args = parser.parse_args()

    if not args.quiet:
        print(quote(args.output))
    df = pd.DataFrame()
    for path in args.input:
        df = pd.concat([df, flatten_freesurfer_stats(os.path.join(args.subject, path))], axis=1)
    df.to_csv(args.output)
