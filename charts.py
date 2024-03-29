import datetime
import logging
import matplotlib
import numpy as np
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator
from matplotlib.ticker import MultipleLocator

import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

WIDTH_INCHES = 16
HEIGHT_INCHES = 9
FG = 'k'
BG = 'w'


def auto_scale(val):
    factor = 1
    t = val
    while t > 10:
        factor = factor * 10
        t = int(t / 10)
    return (t + 1) * factor


def no_zero(n):
    if n == 0:
        return None
    return n


# JEFF this should use a python generator
# or pandas

def next_bin_date(d, size):
    if size == 7:
        return d + datetime.timedelta(days=7)
    else:
        month = d.month + 1
        if month > 12:
            month = 1
            year = d.year + 1
        else:
            year = d.year
        return datetime.date(year, month, 1)


def make_bins(dates, data):
    logging.debug('make_bins called with %d items' % len(dates))
    days = (dates[-1] - dates[0]).days
    if days <= 731:  # 2 years or less -- don't bin! leave as daily data
        return dates, data
    if days <= 3650:  # 10 years or less -- bin into weeks
        bin_start_date = dates[0]
        bin_size = 7
        bin_end_date = next_bin_date(bin_start_date, bin_size)
    else:  # bin into months
        bin_start_date = datetime.date(dates[0].year, dates[0].month, 1)
        bin_size = 31
        bin_end_date = next_bin_date(bin_start_date, bin_size)

    binned_dates = []
    binned_data = []

    for i in range(len(data)):
        binned_data.append([])
    bin_total = [0] * len(data)

    for i in range(0, len(dates)):
        d = dates[i]
        while d > bin_end_date:
            binned_dates.append(bin_start_date)
            for j in range(len(data)):
                binned_data[j].append(bin_total[j])
                bin_total[j] = 0
            bin_start_date = bin_end_date
            bin_end_date = next_bin_date(bin_start_date, bin_size)

        for j in range(len(data)):
            bin_total[j] += data[j][i]

    binned_dates.append(bin_start_date)
    for j in range(len(data)):
        binned_data[j].append(bin_total[j])
        bin_total[j] = 0

    logging.debug('make_bins returning %d items' % len(binned_dates))
    return binned_dates, binned_data


def plot_activity(time_series, title, filename=None, start_date=None, end_date=None):
    """
    make the chart
    """
    logging.debug('plot_activity(...,%s, %s)' % (title, filename))

    max_duration = 0.0
    talk_groups = {}
    for item in time_series:
        for k, v in item.items():
            if k != 'date':
                count = v['count']
                duration = v['duration']
                dd = talk_groups.get(k)
                if dd is None:
                    dd = {'talk_group': k, 'count': 0, 'duration': 0.0}
                    talk_groups[k] = dd
                if duration > dd['duration']:
                    dd['duration'] = duration
                if count > dd['count']:
                    dd['count'] = count
                if duration > max_duration:
                    max_duration = duration

    talk_groups_list = list(talk_groups.values())
    talk_groups_list = sorted(talk_groups_list, key=lambda ctg: ctg['duration'], reverse=True)
    talk_groups_list = talk_groups_list[:10]
    max_duration = talk_groups_list[0]['duration'] / 60.0

    interesting_talk_groups = []
    for tg in talk_groups_list:
        interesting_talk_groups.append(tg['talk_group'])

    # interesting_talk_groups = interesting_talk_groups[:10]  # force reasonable length

    data = []
    for i in range(0, len(interesting_talk_groups) + 1):
        data.append([])

    for i in range(0, len(time_series)):
        item = time_series[i]
        data[0].append(item['date'])
        for j in range(0, len(interesting_talk_groups)):
            tg_name = interesting_talk_groups[j]
            tg_data = item.get(tg_name)
            if tg_data is not None:
                duration = tg_data['duration'] / 60.0
                if len(data[j + 1]) > 1 and data[j + 1][-1] is None:
                    data[j + 1][-1] = 0.0
            else:
                duration = 0.0
                if len(data[j + 1]) > 1 and data[j + 1][-1] == 0.0:
                    duration = None
            data[j + 1].append(duration)

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)
    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')
    dates = matplotlib.dates.date2num(data[0])
    start_date = time_series[0]['date']
    end_date = time_series[-1]['date']
    ax.set_xlim(start_date, end_date)
    y_axis_multiple = 10
    y_max = (int(max_duration / y_axis_multiple) + 1) * y_axis_multiple
    ax.set_ylim(0, y_max)

    # 11 colors, linestyles, markers?
    colors = ['r', 'g', 'b', 'c', '#990099', '#ff6600', '#00ff00', '#663300', '#00ff99', 'k', '#990099']
    line_styles = ['-', '-', '-', '-', '-', ':', '--', ':', '--', '--', '-.']  # -.
    marker_style = ['o', 'v', 's', 'p', 'P', '*', 'h', 'X', 'd', '8', 'x']
    for i in range(0, len(interesting_talk_groups)):
        ax.plot_date(dates, data[i + 1], color=colors[i],
                     linestyle=line_styles[i],
                     # marker=marker_style[i],
                     # markersize=0,
                     marker='',
                     label='{:s}'.format(interesting_talk_groups[i]))

    ax.grid(True)

    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('Usage Minutes', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('UTC Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(WeekdayLocator(byweekday=6))  # sunday
    ax.xaxis.set_minor_locator(DayLocator())  # every day
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
    ax.tick_params(axis='x', labelrotation=90)

    ax.yaxis.set_major_locator(MultipleLocator(30))

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    return


def plot_activity_stackbar(time_series, title, filename=None, start_date=None, end_date=None):
    """
    make a stacked bar chart of the various talkgroup activity.
    """
    logging.debug('plot_activity_stackbar(...,%s, %s)' % (title, filename))

    max_duration = 0.0
    talk_groups = {}
    for item in time_series:
        for k, v in item.items():
            if k != 'date' and not k.lower().startswith('unknown'):
                count = v['count']
                duration = v['duration']
                dd = talk_groups.get(k)
                if dd is None:
                    dd = {'talk_group': k, 'count': 0, 'duration': 0.0}
                    talk_groups[k] = dd
                if duration > dd['duration']:
                    dd['duration'] = duration
                if count > dd['count']:
                    dd['count'] = count
                if duration > max_duration:
                    max_duration = duration

    talk_groups_list = list(talk_groups.values())
    talk_groups_list = sorted(talk_groups_list, key=lambda ctg: ctg['duration'], reverse=True)
    talk_groups_list = talk_groups_list[:10]

    interesting_talk_groups = []
    for tg in talk_groups_list:
        interesting_talk_groups.append(tg['talk_group'])

    data = []
    # data[0] is list of dates
    for i in range(0, len(interesting_talk_groups) + 1):
        data.append([])

    max_duration = 0.0
    for i in range(0, len(time_series)):
        item = time_series[i]
        data[0].append(item['date'])
        bin_total_duration = 0.0
        for j in range(0, len(interesting_talk_groups)):
            tg_name = interesting_talk_groups[j]
            tg_data = item.get(tg_name)
            if tg_data is not None:
                duration = tg_data['duration'] / 60.0
            else:
                duration = 0.0
            data[j + 1].append(duration)
            bin_total_duration += duration
            if bin_total_duration > max_duration:
                max_duration = bin_total_duration

    fig = plt.Figure(figsize=(WIDTH_INCHES, HEIGHT_INCHES), dpi=100, tight_layout=True)
    ax = fig.add_subplot(111, facecolor=BG)
    ax.set_title(title, color=FG, size='xx-large', weight='bold')
    dates = matplotlib.dates.date2num(data[0])
    #start_date = time_series[0]['date']
    #end_date = time_series[-1]['date']
    start_date = data[0][0]
    end_date = data[0][-1]
    ax.set_xlim(start_date, end_date)
    y_axis_multiple = 10
    y_max = (int(max_duration / y_axis_multiple) + 1) * y_axis_multiple
    ax.set_ylim(0, y_max)
    num_bins = len(data[0])
    logging.info('bins = {}'.format(num_bins))
    if num_bins >= 300:
        width = 0.08  # this seems OK
    elif num_bins >= 200:
        width = 0.06  # ??
    else:
        width = 0.04
    logging.info('width = {}'.format(width))

    cmap = matplotlib.cm.get_cmap('tab10')
    bar_offset = np.zeros((len(dates)), dtype=np.float_)
    for i in range(0, len(interesting_talk_groups)):
        bar_data = np.array(data[i + 1])
        ax.bar(dates, bar_data,
               width,
               align='edge',
               bottom=bar_offset,
               color=cmap.colors[i],
               label=interesting_talk_groups[i],
               linewidth=0.0,
               )
        bar_offset += bar_data

    ax.grid(True)
    ax.tick_params(axis='y', colors=FG, which='both', direction='out', right=False)
    ax.tick_params(axis='x', colors=FG, which='both', direction='out', top=False)
    ax.set_ylabel('Usage Minutes', color=FG, size='x-large', weight='bold')
    ax.set_xlabel('UTC Date', color=FG, size='x-large', weight='bold')

    ax.xaxis.set_major_locator(WeekdayLocator(byweekday=6))  # sunday
    ax.xaxis.set_minor_locator(DayLocator())  # every day
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d'))
    ax.tick_params(axis='x', labelrotation=90)

    ax.yaxis.set_major_locator(MultipleLocator(30))

    legend = ax.legend(loc='upper left', numpoints=1, facecolor=BG, edgecolor=FG)
    for text in legend.get_texts():
        text.set_color(FG)

    ax.spines['left'].set_color(FG)
    ax.spines['right'].set_color(FG)
    ax.spines['top'].set_color(FG)
    ax.spines['bottom'].set_color(FG)

    if filename is not None:
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(filename, facecolor=BG)
    else:
        plt.show()
    plt.close(fig)
    return
