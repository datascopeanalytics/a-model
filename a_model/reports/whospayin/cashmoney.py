import datetime
import ipdb
import dateutil
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import matplotlib.dates as dates


SMALL_CUSTOMER_THRESHOLD = 20000
START = datetime.datetime(2015,1,1,0,0)
END = datetime.datetime(2017,1,1,0,0)

# for merging clients and/or user-friendly names
client_name_map = {"Groupe Atallah Inc": "SSENSE",
                   "Thomson Reuters Global Resources:Map of science prototype":\
                   "Thomson Reuters Global Resources",
                   "Stanford University:oDesk deidentification":\
                   "Stanford University",
                   "Oracle:Oracle retainer":"Oracle",
                   "University of Michigan, Center for Entrepreneurship":\
                   "University of Michigan",
}

#quickbooks weirdness
clients_to_ignore = ["Yoke Peng  Leong"]

def get_customer_quarters_df():
    xl = pd.ExcelFile("sales.xls")
    df = xl.parse("Worksheet")

    #clean up the dataframe
    df = df[~df["Customer"].isin(clients_to_ignore)]
    df.replace({"Customer": client_name_map},inplace=True)

    all_customers = set(df['Customer'])

    customer_history = df.groupby('Customer')['Total'].sum().reset_index()
    customer_history['logged_total']=customer_history['Total'].apply(numpy.log10)
    small_customers = set(customer_history[customer_history['Total'] < SMALL_CUSTOMER_THRESHOLD]["Customer"])

    quarter_string = pd.to_datetime(df['Date']).dt.quarter.astype('str')
    year_string = pd.to_datetime(df['Date']).dt.year.astype('str')
    mid_quarter_month = pd.to_datetime(df['Date']).dt.quarter*3-1
    mid_quarter_day = mid_quarter_month.astype('str') + "-15"
    df['quarter'] = year_string.str.cat(quarter_string, sep='-')
    df['quarter_date'] = year_string.str.cat(mid_quarter_day, sep='-')
    df['quarter_datetime'] = df['quarter_date'].apply(dateutil.parser.parse)

    customer_total_by_quarter = df.groupby(['Customer','quarter_datetime']).sum()['Total'].reset_index()

    customer_quarters = pd.DataFrame()
    quarters = set(customer_total_by_quarter['quarter_datetime'])
    for quarter in quarters:
        _ = customer_total_by_quarter[customer_total_by_quarter['quarter_datetime'] == quarter]
        for row in _.iterrows():
            customer = row[1]['Customer']
            total = row[1]['Total']
            if customer in small_customers:
                customer = "small_customers"
            customer_quarters.set_value(quarter, customer, total)

    customer_quarters.sort_index(inplace=True)

    return customer_quarters

def make_fig(customer_quarters_filtered,fig_save_path,fig_type = 'bar'):

    plt.close('all')

    if fig_type == 'bar':
        ax = customer_quarters_filtered.plot.bar(stacked=True,  width=.9)
    elif fig_type == 'area':
        ax = customer_quarters_filtered.plot.area(linewidth=0)

    # this could be more dynamic
    ticks_labels = [
                    'Q1 2015', 'Q2 2015', 'Q3 2015', 'Q4 2015',
                    'Q1 2016', 'Q2 2016', 'Q3 2016', 'Q4 2016',
                    ]

    ax.set_xticklabels(ticks_labels)

    plt.title('Invoiced Revenue by Quarter')
    plt.ylabel('Invoiced Revenue ($)')
    plt.xlabel('Quarter')

    lgd = ax.legend_
    lgd.set_bbox_to_anchor((1.05, 1.05))
    ax.set_xticklabels(ax.xaxis.get_majorticklabels(), rotation=90)
    plt.savefig(fig_save_path, bbox_extra_artists=(lgd,), bbox_inches='tight')

if __name__ == '__main__':
    customer_quarters = get_customer_quarters_df()
    customer_quarters_filtered = customer_quarters[customer_quarters.index >= START]
    customer_quarters_filtered = customer_quarters_filtered[customer_quarters_filtered.index <= END]
    make_fig(customer_quarters_filtered,"rev_by_customer_quarter_bar.png",fig_type = 'bar')
    make_fig(customer_quarters_filtered,"rev_by_customer_quarter_area.png",fig_type = 'area')



# scratch code
# first_two_quarters_rev = {}
# first_year_quarters_rev = {}
# total_all_time_rev = dict(zip(customer_history['Customer'],customer_history['Total']))
#
# for c in all_customers:
#     try:
#         cust_df_col = customer_quarters[c]
#         first_q_index = cust_df_col.index.get_loc(cust_df_col.first_valid_index())
#         first_two_quarters = cust_df_col[first_q_index:first_q_index+2].sum()
#         first_two_quarters_rev[c] = first_two_quarters
#
#         first_year = cust_df_col[first_q_index:first_q_index+4].sum()
#         first_year_quarters_rev[c] = first_year
#     except KeyError as e:
#         pass
#     # cust_df_col = customer_quarters[c]


# print first_two_quarters_rev
# print
# print first_year_quarters_rev
#
# def plot_top_custs():
#     top_customers = customer_history.sort_values(['Total'], ascending=False).set_index(['Customer'])['Total']
#     top_customers = top_customers[top_customers < SMALL_CUSTOMER_THRESHOLD]
#     ax = top_customers.plot.bar(width=1)
#     plt.title('Datascope Clients with < ${} Invoiced Revenue'.format(SMALL_CUSTOMER_THRESHOLD))
#     plt.ylabel('Invoiced Revenue ($)')
#     plt.savefig('small_customers.png',bbox_inches='tight')
#
# kk = pd.DataFrame([total_all_time_rev,first_two_quarters_rev,first_year_quarters_rev]).transpose()
# kk.columns = ["Total All Time", "First Two Quarters", "First Year"]
# kk["% first two quarters"] = kk["First Two Quarters"]/kk["Total All Time"]
# kk["% first year"] = kk["First Year"]/kk["Total All Time"]
# kk = kk.sort_values(['Total All Time'], ascending=False)
# kk = kk[kk['Total All Time'] > 20000]
# #
# # kk[["Total All Time","% first two quarters","% first year"]]
# # # plot_top_custs()
# # ipdb.set_trace()
# ipdb.set_trace()
