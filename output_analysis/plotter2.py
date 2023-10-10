import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colormaps, cm
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from collections import defaultdict

theme_colors = defaultdict(lambda x: "black")
theme_colors.update(
    {
        "green": "#32CD32",
        "plum": "#DDA0DD",
        "purple": "#8A2BE2",
        "chocolate": "#D2691E",
        "yellow": "#FFD700",
        "blue": "#229A00",
        "red": "#F97306",
        "brown": "#85200C",
        "turquoise": "#00c99e",
        "maroon": "#85200C",
        "pink": "#FF69B4",
        "indianred": "#CD5C5C",
        "darkblue": "#A0CBE8",
        "beige": "#F5F5DC",
    }
)
### function to normalize data based on direction of preference and whether each objective is minimized or maximized
###   -> output dataframe will have values ranging from 0 (which maps to bottom of figure) to 1 (which maps to top)
def reorganize_objs(obj_df, columns_axes, ideal_direction, minmaxs):
    ### if min/max directions not given for each axis, assume all should be maximized
    if minmaxs is None:
        minmaxs = ['max']*len(columns_axes)
         
    ### get subset of dataframe columns that will be shown as parallel axes
    objs_reorg = obj_df[columns_axes].copy()
     
    ### reorganize & normalize data to go from 0 (bottom of figure) to 1 (top of figure), 
    ### based on direction of preference for figure and individual axes
    if ideal_direction == 'bottom':
        tops = objs_reorg.min(axis=0)
        bottoms = objs_reorg.max(axis=0)
        for i, minmax in enumerate(minmaxs):
            if minmax == 'max':
                objs_reorg.loc[:, columns_axes[i]] = (objs_reorg.loc[:, columns_axes[i]].max(axis=0) - objs_reorg.loc[:, columns_axes[i]]) / \
                                        (objs_reorg.loc[:, columns_axes[i]].max(axis=0) - objs_reorg.loc[:, columns_axes[i]].min(axis=0))
            else:
                bottoms[i], tops[i] = tops[i], bottoms[i]
                objs_reorg.loc[:, columns_axes[-1]] = (objs_reorg.loc[:, columns_axes[-1]] - objs_reorg.loc[:, columns_axes[-1]].min(axis=0)) / \
                                         (objs_reorg.loc[:, columns_axes[-1]].max(axis=0) - objs_reorg.loc[:, columns_axes[-1]].min(axis=0))
    elif ideal_direction == 'top':
        tops = objs_reorg.max(axis=0)
        bottoms = objs_reorg.min(axis=0)
        for i, minmax in enumerate(minmaxs):
            if minmax == 'max':
                objs_reorg.loc[:, columns_axes[i]] = (objs_reorg.loc[:, columns_axes[i]] - objs_reorg.loc[:, columns_axes[i]].min(axis=0)) / \
                                        (objs_reorg.loc[:, columns_axes[i]].max(axis=0) - objs_reorg.loc[:, columns_axes[i]].min(axis=0))
            else:
                bottoms[i], tops[i] = tops[i], bottoms[i]
                objs_reorg.loc[:, columns_axes[i]] = (objs_reorg.loc[:, columns_axes[i]].max(axis=0) - objs_reorg.loc[:, columns_axes[i]]) / \
                                        (objs_reorg.loc[:, columns_axes[i]].max(axis=0) - objs_reorg.loc[:, columns_axes[i]].min(axis=0))
 
    return objs_reorg, tops, bottoms

### function to get color based on continuous color map or categorical map
def get_color(value, color_by_continuous, color_palette_continuous, 
              color_by_categorical, color_dict_categorical):
    if color_by_continuous is not None:
        color = colormaps.get_cmap(color_palette_continuous)(value)
    elif color_by_categorical is not None:
        color = color_dict_categorical[value]
    return color

### function to get zorder value for ordering lines on plot. 
### This works by binning a given axis' values and mapping to discrete classes.
def get_zorder(norm_value, zorder_num_classes, zorder_direction):
    xgrid = np.arange(0, 1.001, 1/zorder_num_classes)
    if zorder_direction == 'ascending':
        return 4 + np.sum(norm_value > xgrid)
    elif zorder_direction == 'descending':
        return 4 + np.sum(norm_value < xgrid)

### customizable parallel coordinates plot
def custom_parallel_coordinates(
        obj_df,
        columns_axes=None,
        axis_labels=None,
        units=None,
        ideal_direction=None,
        directions=None, 
        color_by_continuous=None,
        color_palette_continuous=None,
        colorbar_ticks_continuous=None,
        color_by_categorical=None,
        color_categories=None,
        zorder_by=None, 
        zorder_num_classes=10, 
        zorder_direction='ascending',
        alpha_base=1, 
        brushing_dict=None, 
        alpha_brush=0.15,
        lw_base=7,
        fontsize=22, 
        figsize=(37.5, 12),
        save_fig_filename=None,
):
    """
    Generate a customizable parallel coordinates plot for visualizing multidimensional data.

    Parameters:
        obj_df (pd.DataFrame): The input DataFrame containing the data to be visualized.
        columns_axes (list, optional): List of column names of interest from the DataFrame to be used as axes. Defaults to None.
        axis_labels (list, optional): List of labels for the corresponding columns_axes. Defaults to None.
        units (list, optional): List of unit labels corresponding to each axis. Defaults to None.
        ideal_direction (str, optional): The direction of the ideal values along the parallel axes ('top' or 'bottom'). Defaults to None.
        directions (dictionary, optional): Dictionary with column/axis as key and direction as value, indicating whether 'min' or 'max' is the actual ideal value. Defaults to None.
        color_by_continuous (str, optional): The column name for continuous data to color the lines. Defaults to None.
        color_palette_continuous (str or list, optional): The color palette for continuous data. It can be a string representing a predefined seaborn palette or a list of custom colors. Defaults to None.
        colorbar_ticks_continuous (list, optional): List of tick values for colorbar of continuous data. Defaults to None.
        color_by_categorical (str, optional): The column name for categorical data to color the lines. Defaults to None.
        color_dict_categorical (dict, optional): Dictionary mapping categorical values to specific colors. Defaults to None.
        zorder_by (str, optional): The column name used for z-ordering the lines, affecting their rendering order. Defaults to None.
        zorder_num_classes (int, optional): Number of classes for z-ordering. Defaults to 10.
        zorder_direction (str, optional): Direction of z-ordering ('ascending' or 'descending'). Defaults to 'ascending'.
        alpha_base (float, optional): Base alpha value for the lines. Defaults to 0.8.
        brushing_dict (dict, optional): Dictionary containing brushing criteria. Keys are column indices, and values are tuples (threshold, operator). Defaults to None.
        alpha_brush (float, optional): Alpha value for brushed lines. Defaults to 0.05.
        lw_base (float, optional): Base line width for the plot. Defaults to 1.5.
        fontsize (int, optional): Font size for text and labels. Defaults to 22.
        figsize (tuple, optional): Figure size (width, height) in inches. Defaults to (37.5, 12).
        save_fig_filename (str, optional): File path to save the generated plot as an image. Defaults to None.

    Raises:
        AssertionError: If the inputs do not take supported values.

    Returns:
        matplotlib.figure.Figure: The generated parallel coordinates plot.
        matplotlib.axes._subplots.AxesSubplot: The generated subplot.
    """
    ### verify that all inputs take supported values
    assert ideal_direction in ['top', 'bottom']
    assert all(value in ['min', 'max'] for value in directions.values())
    ### plot can only be categorical or continious
    assert color_by_continuous is None or color_by_categorical is None

    if columns_axes is None:
        columns_axes = obj_df.columns
    if axis_labels is None:
        axis_labels = columns_axes

        # Assuming you have columns_axes and axis_labels lists defined already
    col_axis_dict = dict(zip(columns_axes, axis_labels))


    ### create figure
    ### 'hspace, wspace: the height and width spacing between subplots in percentage of the height/width of each subplot
    fig,ax = plt.subplots(1,1, figsize=figsize, gridspec_kw={'hspace':0.1, 'wspace':0.1})

    # Verify that every column in columns_axes has a corresponding direction in directions_dict
    for column in columns_axes:
        if column not in directions:
            raise ValueError(f"Direction not specified for column: {column}")
    # Extract a list of directions for specified columns in columns_axes
    minmaxs = [directions[column] for column in columns_axes]
    ### reorganize & normalize objective data
    objs_reorg, tops, bottoms = reorganize_objs(obj_df, columns_axes, ideal_direction, minmaxs)

    ### apply any brushing criteria
    if brushing_dict is not None:
        satisfice = np.zeros(obj_df.shape[0]) == 0.
        ### iteratively apply all brushing criteria to get satisficing set of solutions
    
        for col_idx, (threshold, operator) in brushing_dict.items():
            if operator == '!=':
                # Brush rows where the categorical column matches the specified category
                satisfice = np.logical_and(satisfice, obj_df.loc[:,col_idx] != threshold)
            if operator == '<':
                satisfice = np.logical_and(satisfice, obj_df.loc[:,col_idx] < threshold)
            elif operator == '<=':
                satisfice = np.logical_and(satisfice, obj_df.loc[:,col_idx] <= threshold)
            elif operator == '>':
                satisfice = np.logical_and(satisfice, obj_df.loc[:,col_idx] > threshold)
            elif operator == '>=':
                satisfice = np.logical_and(satisfice, obj_df.loc[:,col_idx] >= threshold)
 
            ### add rectangle patch to plot to represent brushing
            if operator != '!=':
                threshold_norm = (threshold - bottoms[col_idx]) / (tops[col_idx] - bottoms[col_idx])
                if ideal_direction == 'top' and minmaxs[col_idx] == 'max':
                    if operator in ['<', '<=']:
                        rect = Rectangle([col_idx-0.05, threshold_norm], 0.1, 1-threshold_norm)
                    elif operator in ['>', '>=']:
                        rect = Rectangle([col_idx-0.05, 0], 0.1, threshold_norm)
                elif ideal_direction == 'top' and minmaxs[col_idx] == 'min':
                    if operator in ['<', '<=']:
                        rect = Rectangle([col_idx-0.05, 0], 0.1, threshold_norm)
                    elif operator in ['>', '>=']:
                        rect = Rectangle([col_idx-0.05, threshold_norm], 0.1, 1-threshold_norm)
                if ideal_direction == 'bottom' and minmaxs[col_idx] == 'max':
                    if operator in ['<', '<=']:
                        rect = Rectangle([col_idx-0.05, 0], 0.1, threshold_norm)
                    elif operator in ['>', '>=']:
                        rect = Rectangle([col_idx-0.05, threshold_norm], 0.1, 1-threshold_norm)
                elif ideal_direction == 'bottom' and minmaxs[col_idx] == 'min':
                    if operator in ['<', '<=']:
                        rect = Rectangle([col_idx-0.05, threshold_norm], 0.1, 1-threshold_norm)
                    elif operator in ['>', '>=']:
                        rect = Rectangle([col_idx-0.05, 0], 0.1, threshold_norm)
                     
                pc = PatchCollection([rect], facecolor='grey', alpha=0.5, zorder=3)
                ax.add_collection(pc)

    ### loop over all solutions/rows & plot on parallel axis plot
    for i in range(objs_reorg.shape[0]):
        if color_by_continuous is not None:
            color_dict_categorical=None
            color = get_color(objs_reorg.loc[i,color_by_continuous], 
                              color_by_continuous, color_palette_continuous,
                              color_by_categorical, color_dict_categorical)
        elif color_by_categorical is not None:
            color_palette = list(theme_colors.values())[:len(color_categories)]

            ### Zip created_vars_names and color_palette, then convert it to a dictionary
            color_dict_categorical = dict(zip(color_categories, color_palette))
            ### Add 'general': 'gray' as the first key-value pair
            color_dict_categorical.update({'other': 'gray'})
            
            color = get_color(obj_df.loc[i,color_by_categorical], 
                              color_by_continuous, color_palette_continuous,
                              color_by_categorical, color_dict_categorical)
                         
        ### order lines according to ascending or descending values of one of the objectives?
        if zorder_by is None:
            zorder = 4
        else:
            zorder = get_zorder(objs_reorg.loc[i,zorder_by], 
                                zorder_num_classes, zorder_direction)
             
        ### apply any brushing?
        if brushing_dict is not None:
            if satisfice.loc[i]:
                alpha = alpha_base
                lw = lw_base
            else:
                alpha = alpha_brush
                lw = 7
                zorder = 2
        else:
            alpha = alpha_base
            lw = lw_base
             
        ### loop over objective/column pairs & plot lines between parallel axes
        for j in range(objs_reorg.shape[1]-1):
            y = [objs_reorg.iloc[i, j], objs_reorg.iloc[i, j+1]]
            x = [j, j+1]
            ax.plot(x, y, c=color, alpha=alpha, zorder=zorder, lw=lw)
             
             
    ### add top/bottom ranges with one decimal point precision
    for j in range(len(columns_axes)):
        ax.annotate(f"{tops[j]:.1f}", [j, 1.02], ha='center', va='bottom', 
                    zorder=5, fontsize=fontsize)
        ax.annotate(f"{bottoms[j]:.1f}", [j, -0.02], ha='center', va='top', 
                    zorder=5, fontsize=fontsize)  
        ax.plot([j,j], [0,1], c='k', zorder=1)
     
    ### other aesthetics
    ax.set_xticks([])
    ax.set_yticks([])
     
    for spine in ['top','bottom','left','right']:
        ax.spines[spine].set_visible(False)
    
    ### a subtle arrow on top of the text pointing at the direction of the axes
    arrow_text = "Direction of Preference $\\rightarrow$" if ideal_direction == 'top' else "Direction of Preference $\\leftarrow$"

    ax.annotate(
        arrow_text,
        xy=(len(columns_axes) -0.6, 0.5),
        color="#636363",
        fontsize=fontsize,
        rotation=90,
        ha="left",
        va="center",
    )

 
    ### !! push adjustment !!
    ax.set_xlim(-0.4, len(columns_axes) - 0.2)
    ax.set_ylim(-0.4,1.1)
     
    for i, (label, unit) in enumerate(zip(axis_labels, units)):
        ax.annotate(f"{label}\n[{unit}]", xy=(i, -0.12), ha='center', va='top', fontsize=fontsize)
    ax.patch.set_alpha(0)
     
 
    ### colorbar for continuous legend
    if color_by_continuous is not None:
        mappable = cm.ScalarMappable(cmap=color_palette_continuous)
        mappable.set_clim(vmin=obj_df[color_by_continuous].min(), 
                          vmax=obj_df[color_by_continuous].max())
        cb = plt.colorbar(mappable, ax=ax, orientation='horizontal', shrink=0.4, 
                          label=col_axis_dict[color_by_continuous], pad=0.03, 
                          alpha=alpha_base)
        if colorbar_ticks_continuous is not None:
            _ = cb.ax.set_xticks(colorbar_ticks_continuous, colorbar_ticks_continuous, 
                                 fontsize=fontsize)
        _ = cb.ax.set_xlabel(cb.ax.get_xlabel(), fontsize=fontsize)  
    ### categorical legend
    elif color_by_categorical is not None:
        leg = []
        for label,color in color_dict_categorical.items():
            leg.append(Line2D([0], [0], color=color, lw=7, 
                              alpha=alpha_base, label=label))
        _ = ax.legend(handles=leg, loc='upper center', 
                      ncol=4,
                      bbox_to_anchor=[0.5,-0.07], frameon=False, fontsize=22)
         
    ### save figure
    if save_fig_filename is not None:
        plt.savefig(save_fig_filename, bbox_inches='tight', dpi=300)