import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import textwrap as tr
from django.conf import settings
from pandas import DataFrame


class DataVisualizer:
    def __init__(self, rel_file_path='Financial Sample.xlsx'):
        my_sheet = 'Sheet1'
        self.df: DataFrame = pd.read_excel(settings.BASE_DIR / rel_file_path, sheet_name=my_sheet)

    def num_of_fields(self):
        return len(self.df.columns)

    def get_all_fields(self):
        return self.df.columns.tolist()

    # Country - Product - Units Sold
    def multi_group_chart(self, groups_col, bars_col, y_col):
        sorted_groups_col = self.df.groupby([groups_col], sort=False)[y_col].sum().sort_values(ascending=False).index

        def sort_countries(keys):
            return [sorted_groups_col.tolist().index(country) for country in keys]

        # grouped_df = self.df.groupby([bars_col, groups_col], sort=False)[y_col].sum().reindex(
        #     sorted_groups_col, level=1)
        grouped_df = self.df.groupby([bars_col, groups_col], sort=False)[y_col].sum().sort_index(
            level=1, key=sort_countries)
        bar_labels = grouped_df.index.get_level_values(0).unique()
        x = np.arange(stop=2*len(sorted_groups_col), step=2)  # the label locations
        group_width = 1  # the width of the bars

        fig, ax = plt.subplots()

        # rects = []
        bar_width = group_width / len(bar_labels)
        cur_pos = -group_width / 2
        for bar_label in bar_labels:
            ax.bar(x + cur_pos, grouped_df[bar_label].values, bar_width, label=bar_label)
            cur_pos += bar_width

            # Store bars for bar labeling
            # rects.append(ax.bar(x + cur_pos, grouped_df[bar_label].values, bar_width, label=bar_label))
            # if bar_label != 'Carretera':
            #     rects.pop()

        # Set Label of value on top of each bar
        # for r in rects:
        #     ax.bar_label(r, padding=3)
        # ax.bar_label(rects, padding=3)

        # ax.set_title('Units Sold  - by Country and Product')
        ax.set_xticks(x)
        ax.set_xticklabels([tr.fill(g, width=10) for g in sorted_groups_col], wrap=True)
        ax.set_ylabel(y_col, labelpad=5, fontweight='bold', wrap=True)
        ax.set_xlabel(groups_col, labelpad=5, fontweight='bold', wrap=True)
        ax.legend()

        fig.suptitle(f'{y_col} by {groups_col} and {bars_col}')
        fig.tight_layout()
        return fig

    # pie chart
    def pie_chart(self, x_col, y_col):
        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        values = self.df.groupby([x_col])[y_col].sum()
        labels = values.index.to_list()
        # labels = [tr.fill(label, width=10) for label in labels]
        # explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')
        explode = [0 for i in range(len(labels))]
        fig, ax = plt.subplots()
        ax.pie(values, explode=explode, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        fig.suptitle(f'{y_col} by {x_col}')
        return fig

    def linear_chart(self, x_col, y_col):
        values = self.df.groupby([x_col])[y_col].sum().sort_values(ascending=False)
        labels = values.index.to_list()
        labels = [tr.fill(label, width=10) for label in labels]
        fig, ax = plt.subplots()
        ax.plot(labels, values)
        plt.xticks(rotation=40)
        plt.subplots_adjust(bottom=0.25)
        ax.set_ylabel(y_col, labelpad=5, fontweight='bold', wrap=True)
        ax.set_xlabel(x_col, labelpad=10, fontweight='bold', wrap=True)

        fig.suptitle(f'{y_col} by {x_col}')
        return fig

    def bar_chart(self, x_col, y_col):
        values = self.df.groupby([x_col])[y_col].sum().sort_values(ascending=False)
        labels = values.index.to_list()
        labels = [tr.fill(label, width=10) for label in labels]
        # fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(9, 3))
        fig, ax = plt.subplots()
        ax.bar(labels, values)
        plt.xticks(rotation=40)
        plt.subplots_adjust(bottom=0.25, left=0.15)
        ax.set_ylabel(y_col, labelpad=5, fontweight='bold', wrap=True)
        ax.set_xlabel(x_col, labelpad=10, fontweight='bold', wrap=True)

        fig.suptitle(f'{y_col} by {x_col}')
        return fig

    # def save_fig(self, rel_file_path):
    #     try:
    #         full_path = settings.MEDIA_ROOT / rel_file_path
    #         plt.savefig(full_path)
    #         return full_path
    #     except Exception as e:
    #         print(str(e))
    #         return False

    def draw_and_save_fig(self, method_name: str, *args, rel_path=None):
        try:
            method_to_call = getattr(self, method_name)
            fig = method_to_call(*args)
            if not rel_path:
                name_str = f'{method_name}_{args[-1]}_by_{args[0]}'
                for i in range(len(args)-2):
                    name_str += f'_and_{args[i+1]}'
                rel_path = f'figs/{name_str}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png'
            full_path = settings.MEDIA_ROOT / rel_path
            fig.savefig(full_path)
            return full_path
        except Exception as e:
            # print("EXCEPTION HAPEND IN CORE.py")
            print(str(e))
            return False

    def show(self):
        plt.show()


# def word_wrapper()
