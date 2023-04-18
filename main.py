import yfinance as yf 
import pandas as pd # for data analysis
# import numpy as np # for data analysis
import csv # for data analysis
import os # to check if files exist
from PySimpleGUI import PySimpleGUI as sg
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



########## WINDOW 2 ##########
def window_wallet():
    sg.theme('Reddit')
    test1 = [
        [sg.Text('Ticket:')],
        [sg.Input(key='ticket', size=(10,1))],
    ]
    test2 = [
        [sg.Text('Number:')],
        [sg.Input(key='number', size=(10,1))],
    ]
    test3 = [
        [sg.Text('Price:')],
        [sg.Input(key='price', size=(10,1))],
    ]
    test4 = [
        [sg.Text('Date:')],
        [sg.Input(key='date', size=(10,1))],
    ]
    layout = [
        [sg.Text('', key='message')],
        [sg.Text('Stock:'), sg.Input(key='stock', size=(20,1)), sg.Button('Show', key='show')],
        [sg.Column(test1), sg.Column(test2), sg.Column(test3), sg.Column(test4)],
        [sg.Button('Add Asset', key='add_asset'), sg.Button('Show Portfolio', key='show_portfolio')],
        ]
    return sg.Window('Wallet page', layout, finalize=True, element_justification='center')

########## WINDOW 1 ##########
def window_login():
    sg.theme('Reddit')
    layout_login = [
        [sg.Text('Username:'), sg.Input(key='username', size=(20,1))],
        [sg.Text('Password:'), sg.Input(key='password', password_char='*', size=(20,1))],
        [sg.Button('Sign In', key='SignIn'), sg.Button('Login')],
    ]
    return sg.Window('Login page', layout_login, finalize=True, element_justification='center')


def check_user(username):
    # file = pd.read_csv('users.txt',sep=" ", header=None)
    # aux = np.where(file[0]=="nes","nes",'False')
    with open("users.txt","r") as file:
        data_users = csv.reader(file, delimiter=' ')
        #table = [row for row in data_users]    # make a table read in line
        table = list(map(list, zip(*data_users)))   # make a table read in colum
    if username in table[0]:
        result = True
    else:
        result = False 
    return result # true or false

def search_user(username, password):
    with open("users.txt","r") as file:
        data_users = csv.reader(file, delimiter=' ')
        #table = [row for row in data_users]    # make a table read in line
        table = list(map(list, zip(*data_users)))   # make a table read in colum
    if username in table[0] and password in table[1]:  
        result = True
        window1['username'].update('')
        window1['password'].update('')
    else:
        result = False 
    return result # true or false



def register_user(username, password):
    user = check_user(username)
    if user == True:
        result = 'User already registered!'
    else:
        with open("users.txt","a+") as file:
            file.writelines(f'\n{username} {password}')
        result = "Successfully registered"
    return sg.popup(result)


def register_wallet(name, ticket, number, price, date):
    if os.path.isfile(f'{name}_wallet.csv') == False:
        file = open(f'{name}.csv', 'a+')
        file.writelines('Ticket,Number,Price,Date\n')
        file.close
    try:
        if isinstance(float(number), float) and isinstance(float(price), float):
            file = open(f'{name}_wallet.csv', 'a+')
            file.writelines(f'{ticket},{number},{price},{date}\n')
            window2['ticket'].update('')
            window2['number'].update('')
            window2['price'].update('')
            window2['date'].update('')
            aux_message = 'Successfully registered'
        else:
            aux_message = 'Check the format of the fields'
    except:
        aux_message = 'Check the format of the fields'
    # file = open(f'{name}.csv', 'a+')
    # file.writelines(f'{ticket},{number},{price},{date}\n')
    return sg.popup(aux_message)


def table_wallet(name):
    # Load wallet with all tradess 
    wallet = pd.read_csv(f'{name}_wallet.csv')
    # wallet = pd.read_csv('joh_wallet.csv')

    # Creating tables for price and quantity with suitable format
    table_price = pd.pivot_table(wallet, values=['Price'], index=['Date'], columns=wallet['Ticket'], fill_value=0)
    table_Qtt = pd.pivot_table(wallet, values=['Quantity'], index=['Date'], columns=wallet['Ticket'], fill_value=0)

    # Adjusting the parameters to apply in yFinance
    date_start = wallet['Date'].min()
    date_end = '2023-04-14'
    indice = table_price.columns.get_level_values(1).to_list()
    quotation = yf.download(indice, date_start, date_end, rounding=True)['Adj Close']
    
    # Removing the levels of Price and Quantity of the tables
    table_price = table_price.droplevel(level=0, axis=1)
    table_Qtt = table_Qtt.droplevel(level=0, axis=1)

    # convert index of the table_Qtt to datetime format
    table_Qtt.index = pd.to_datetime(table_Qtt.index)

    # replace the index of table_Qtt by index of quotation (quotation.index contains all date periode)
    table_Qtt_quo = table_Qtt.reindex(index=quotation.index)

    # change NaN by zero
    table_Qtt_quo.fillna(value=0,inplace=True)

    # replicating the quantity of cotes accumulated over the date period
    Qtt_accum = table_Qtt_quo.cumsum()

    # Calculate the position of the all the assets in the wallet
    wallet_position = Qtt_accum*quotation
    wallet_position['Total'] = wallet_position.sum(axis=1)

    # Coverting the index in datetime format
    table_price.index = pd.to_datetime(table_price.index)

    # Creating a frame with all trades
    trades = (table_Qtt_quo*table_price).sum(axis=1)

    # Calculating the rentability of the wallet
    for i, date in enumerate(trades.index):
        if i == 0:
            wallet_position.at[date, 'vl_cota'] = 1
            wallet_position.at[date, 'qtd_cota'] = wallet_position.loc[date]['Total'].copy()
            #wallet_position.at[date, 'retorno'] = 1
        else:
            if trades[date] != 0:
                wallet_position.at[date, 'qtd_cota'] = wallet_position.iloc[i-1]['qtd_cota'] + (trades[date] / wallet_position.iloc[i-1]['vl_cota'])
                wallet_position.at[date, 'vl_cota'] = wallet_position.iloc[i]['Total'] / wallet_position.at[date, 'qtd_cota']
                wallet_position.at[date, 'retorno'] = wallet_position.iloc[i]['vl_cota'] / wallet_position.iloc[i-1]['vl_cota'] -1
            else:
                wallet_position.at[date, 'qtd_cota'] = wallet_position.iloc[i-1]['qtd_cota']
                wallet_position.at[date, 'vl_cota'] = wallet_position.iloc[i]['Total'] / wallet_position.at[date, 'qtd_cota']
                wallet_position.at[date, 'retorno'] = wallet_position.iloc[i]['vl_cota'] / wallet_position.iloc[i-1]['vl_cota'] -1

    wallet_position['retorno'].plot()
    plt.legend()
    plt.grid()
    plt.show()

    return sg.popup(wallet_position, title='Portfolio')


def create_plot(x_val, y_val, namme):
    plt.plot(x_val, y_val, label=namme)
    plt.xlabel('Date period')
    plt.ylabel('Stock price (R$)')
    plt.legend
    plt.grid
    return plt.gcf()

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg

def info_stock(name_stock):
    # get the information of stock in variable hist
    sft = yf.Ticker(name_stock)
    #hist = sft.history(period="max")
    hist = sft.history(period='actual')
    if hist.empty:
        return sg.popup('Stock not found!')   
    # draw_figure(window2['canva'].TKCanvas, create_plot(hist.index, hist['Close'], name_stock))
    #hh = sft.history(period='actual')
    return sg.popup(hist['Close'])



aux_name = '' # auxiliar to pass 'username' of window1 to window2

window1, window2 = window_login(), None

while True:

    window, event, value = sg.read_all_windows()

    if window == window1 and event == sg.WIN_CLOSED:
        break
    if event == 'SignIn':
        if value['username'] == '' or value['password'] == '':
            sg.popup('Fill all fields')
        else:
            register_user(value['username'], value['password'])
    if event == 'Login':
        user = search_user(value['username'], value['password'])
        if user == True:
            window2 = window_wallet()
            aux_name = value['username']
            window2['message'].update(f"Welcome {aux_name}")
            # window1.hide()
            # window2.write_event_value('username', value['username'])
        else:
            sg.popup('User not found')

    if window == window2 and event == sg.WIN_CLOSED:
        break
    if window == window2 and event == 'show':
        info_stock(value['stock'])
    if window == window2 and event == 'add_asset':
        if value['ticket'] == '' or value['number'] == '' or value['price'] == '' or value['date'] == '':
            sg.popup('Fill all fields')
        else:
            register_wallet(aux_name, value['ticket'], value['number'], value['price'], value['date'])
    if window == window2 and event == 'show_portfolio':
        table_wallet(aux_name)
        

# #     if event == sg.WIN_CLOSED or event == 'Close':
# #         break
# #     if event == 'SignIn':
# #         print(hist.index)
# #         draw_figure(janela['canva'].TKCanvas, create_plot(hist.index, hist['Close'], namme))

# #     namme = value['ticket']



# #     # sum the divendends in year
# #     # dividendo = hist['Dividends'].resample('Y').sum()

    




# # ########################
# # ########################


# # dividendo = hist['Dividends']

# # # plt.plot(dividendo.index.year, dividendo, label='MXRF11')
# # plt.plot(dividendo, label=namme)
# # plt.xlabel('Date period')
# # plt.ylabel('Annual dividend yield  R$')
# # plt.legend()
# # plt.grid()
# # plt.show()

    
