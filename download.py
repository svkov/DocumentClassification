import bs4
import requests
import numpy as np
import pandas as pd
from tqdm import trange, tqdm


def get_urls_tiks(bs, base_url):
    a_with_links = bs.find_all('table')[8].find_all('a', href=True)
    return [base_url + a['href'] for a in a_with_links]


def get_tiks_names(bs):
    a_with_links = bs.find_all('table')[8].find_all('a', href=True)
    return [a.text for a in a_with_links]


def get_columns(bs):
    td = bs.find_all('table')[6].find_all('td')[0]
    table = td.find_all('table')[0]

    columns = []
    for tr in table.find_all('tr'):
        potential_column = tr.find_all('td')[1].text
        if potential_column != '\xa0' and potential_column != 'Сумма':
            columns.append(potential_column)

    assert len(columns) == 14
    return columns


def get_uik_numbers(tr):
    uik_number = []
    for a in tr.find_all('a'):
        uik_number.append(a.text)
    return uik_number


def get_another_number(tr):
    numbers = []
    for b in tr.find_all('b'):
        numbers.append(b.text)
    return numbers


def get_page_numbers_content(all_tr):
    all_tr.pop(11)  # Пустая строка
    assert len(all_tr) == 14
    return [get_another_number(tr) for tr in all_tr]


def get_df(name, columns, uik, numbers):
    full_df = pd.DataFrame(columns=columns)
    for i, (column, number) in enumerate(zip(columns, numbers)):
        values = np.array(number).astype(np.int)
        part_df = pd.DataFrame(dict(zip(uik, values)), index=[column]).T
        full_df[column] = part_df[column]
    full_df['УИК'] = full_df.index
    full_df['ТИК'] = name
    return full_df


def parse_tik_page(url, name, columns):
    response = requests.request('GET', url)
    bs_ = bs4.BeautifulSoup(response.text, features="html.parser")

    all_tr = bs_.find_all('div')[0].find_all('tr')
    uik = get_uik_numbers(all_tr[0])
    all_tr = all_tr[1:]
    numbers = get_page_numbers_content(all_tr)
    return get_df(name, columns, uik, numbers)


def get_full_dataframe(base_url, url):
    response = requests.request('GET', base_url + url)
    bs = bs4.BeautifulSoup(response.text, features="html.parser")

    urls = get_urls_tiks(bs, base_url)
    columns = get_columns(bs)
    names = get_tiks_names(bs)

    df = pd.DataFrame()

    pbar = tqdm()
    pbar.reset(total=len(urls))
    for i, (url, name) in enumerate(zip(urls, names)):
        try:
            parsed_df = parse_tik_page(url, name, columns)
            df = df.append(parsed_df)
        except :
            pass  # Электронные участки
        pbar.update()
    pbar.refresh()
    return df


def main():
    base_url = 'http://notelections.online'
    url = "/region/region/st-petersburg?action=show&root=1&tvd=27820001217417&vrn=27820001217413&region=78&global=&sub_region=78&prver=0&pronetvd=null&vibid=27820001217417&type=222"
    df = get_full_dataframe(base_url, url)
    df.to_csv('data.csv')


if __name__ == '__main__':
    main()