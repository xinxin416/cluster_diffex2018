import os
import argparse

from scio import load_gene_by_cell_matrix
from distance import select_markers, get_correlation, get_distance
from cluster import run_phenograph
from visualize import run_umap, run_dca, plot_clusters

def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--count-matrix', required=True)
    parser.add_argument('-o', '--outdir', required=True)
    parser.add_argument('-p', '--prefix', default='')
    parser.add_argument('--metric', default='spearman',
            choices=['spearman', 'euclidean', 'pearson'])
    parser.add_argument('-d', '--dim-redux',
            choices=['none', 'marker', 'pca', 'marker_pca'])
    parser.add_argument('-k', default=20,
            help='Number of nearest neighbors to use for clustering.')

    # marker selection/loading parameters
    parser.add_argument('-mf', '--marker-file', default='',
            help='Use the given marker file rather than determining highly '
            'variable genes from `count-matrix` (for marker based column '
            'selection).')
    parser.add_argument('--nstd', default=6.0
            help='Only used when `dim-redux`=`marker` and `marker_file` not '
            'given. Sets adaptive threshold for marker selection at `nstd` '
            'standard devations above the mean dropout score. The threshold '
            'used is min(adaptive_threshold, absolute_theshold).')
    parser.add_argument('--absolute-threshold', default=0.15,
            help='Only used when `dim-redux`=`marker` and `marker_file` not '
            'given. Sets absolute threshold for marker selection. The threshold '
            'used is min(adaptive_threshold, absolute_theshold).')
    parser.add_argument('--window-size', default=25, type=int,
            help='Only used when `dim-redux`=`marker` and `marker_file` not '
            'given. Sets size of rolling window used to approximate expected '
            'fraction of cells expressing given the mean expression.')

    # visualization
    parser.add_argument('--tsne', action='store_true', default=False)
    parser.add_argument('--no-tsne', dest='tsne', action='store_false')

    return parser


def _parseargs_post(args):
   return args


if __name__=='__main__':
    parser = _parser()
    args = parser.parse_args()
    args = _parseargs_post(args)

    # load the count matrix
    counts, genes = load_gene_by_cell_matrix(args.count_matrix)

    running_prefix = [args.prefix]
    # select markers or reduce dimensionality
    if args.dim_redux == 'marker':
        if os.path.exits(args.marker_file):
            markers = pd.read_csv(args.marker_file, delim_whitespace=True,
                header=None)
            marker_ix = genes.loc[genes.ens.isin(markers[0])].index.values
            msg = 'Found {} marker gene names in {}. {} matching genes found '
            msg += 'in count matrix.'
            print(msg.format(len(markers), args.marker_file, len(marker_ix)))
        else:
            marker_ix = select_markers(counts, outdir=args.outdir,
                prefix=args.prefix, gene_names=genes,
                window=args.window_size, nstd=args.nstd,
                t=args.absolute_threshold)
        running_prefix.append('markers')
        redux = counts.iloc[marker_ix]
    elif args.dim_redux in ['none', 'pcs']:
        print('{} not yet implemented'.format(args.dim_redux))
        return

    # get similarity/distance
    if args.metric == 'spearman':
        simillarity = get_correlation(redux, outdir=args.outdir,
                prefix='.'.join(running_prefix), verbose=True)
        distance = 1 - simillarity
        running_prefix.append('corrSP')
    else:
        print('{} not yet implemented'.format(args.metric))
        return

    # visualize
    umap = run_umap(distance, prefix='.'.join(running_prefix),
            outdir=arg.outdir)
    dca = run_dca(distance, prefix='.'.join(running_prefix), outdir=args.outdir)
    if args.tsne:
        print('tsne not yet implemented')

    # cluster
    communities, graph, Q = run_phenograph(distance, k=args.k,
            prefix='.'.join(running_prefix), outdir=args.outdir)
    # visualize communities
    plot_clusters(communities, umap, outdir=outdir,
            prefix='.'.join(running_prefix + 'umap'))
    plot_clusters(communities, dca, outdir=outdir,
            prefix='.'.join(running_prefix + 'dca'),
            label_name='Diffusion Component')

    # differential expression
    # TODO
