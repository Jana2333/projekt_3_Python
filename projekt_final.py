import requests
import csv
import bs4
import os
import sys
import pandas as pd

def write_moduls_versions():
    rq=requests.__version__
    bs=bs4.__version__
    ss=sys.version.split()[0]
    knihovny=['request','csv','bs4','sys','os','pandas']
    knihovny_zkratky=[rq,ss,bs,ss,ss,ss]
    with open('requirements.txt','w') as r:
        for i in range(len(knihovny)):
            r.write(f'Knihovna {knihovny[i]}, verze {knihovny_zkratky[i]}.\n')
write_moduls_versions()

def main():
    web=vstup_uzivatele()
    data=nacteni_webu(web[0])
    soubor=web[1]
    kod_obce=kody_obci(data)
    nazev_obce=nazvy_obci(data)
    okrsky=vyber_okrsku(data)
    prehled=volici_obalky_hlasy_strany(okrsky,data)
    tabulka=souhrnna_tabulka(kod_obce,nazev_obce,prehled[0],prehled[1])
    zapis_do_souboru(tabulka[0],tabulka[1],soubor)
    print('Ukoncuji election scraper.')
    
def vstup_uzivatele():
    if len(sys.argv)!=3:
        print('Nezadal jsi spravny pocet argumentu.')
        exit()
    jmeno_webu=sys.argv[1]
    jmeno_souboru=sys.argv[2]
    if jmeno_webu != web:
        print('Nezadal jsi spravny web.')
        exit()
    elif jmeno_souboru.endswith('.csv')==False:
        print('Chybny format souboru.')
        exit()
    else:
        print(f'Stahuji data z vybraneho URL: {jmeno_webu}')
    return jmeno_webu, jmeno_souboru

def nacteni_webu(web):
    r=requests.get(web)
    soup=bs4.BeautifulSoup(r.text,'html.parser')
    return soup

def kody_obci(data):
    kod_obce=[]
    for i in data.select('td.cislo'):
        kod_obce.append(i.text)
    return kod_obce

def nazvy_obci(data):
    nazev_obce=[]
    for i in data.select('td.overflow_name'):
        nazev_obce.append(i.text)
    return nazev_obce
    
def vyber_okrsku(data):
    zacatek_webu='https://volby.cz/pls/ps2017nss/'
    vyber_okrsku=[] 
    okrsky=[]

    for i in data.select('td.center a'):
        vyber_okrsku.append(zacatek_webu+i['href'])
    
    for i in vyber_okrsku:
        r1=requests.get(i)
        stranka_obce=bs4.BeautifulSoup(r1.text,'html.parser')
        if stranka_obce.select('td.cislo a'): 
            jednotlive_okrsky=[]
            for j in stranka_obce.select('td.cislo a'): 
                jednotlive_okrsky.append(zacatek_webu+j['href'])
            okrsky.append(jednotlive_okrsky)
        else: 
            if stranka_obce.select('div.tab_full_ps311 a'): 
                okrsek=stranka_obce.find_all('a')
                for k in okrsek:
                    if k.text=='úplné zobrazení':
                        okrsky.append(zacatek_webu+k['href'])
            else:
                okrsky.append(i)
    
    return okrsky
     
def premena_na_cislo(cislo):
    cisla=[]
    for i in cislo:
        if '\xa0' in i:
            pozice=i.find('x')
            nove_cislo=i[:pozice-1]+i[pozice+4:]
            nove_cislo_seznam=[]
            for j in nove_cislo:
                nove_cislo_seznam.append(j)
            i=''
            for j in nove_cislo_seznam:
                if j != '\xa0':
                    i+=j
        cisla.append(i)
    return cisla

def filtrace(web):
    vyber_id=[]
    vyber_headers=[]
    vyber_id_headers=[]
    for i in range(2,8):
        vyber_id_headers.append(f'sa{i}')
    for i in filter(lambda x: x!='\n',web.body.main.div.table.children):
        for j in filter(lambda x: x!='\n',i.children):
            for k in vyber_id_headers:
                if k==j.attrs.get('id'):
                    vyber_id.append(j.text)
                if [k]==j.attrs.get('headers'):
                    vyber_headers.append(j.text)
    return vyber_id, vyber_headers

def volici_obalky_hlasy_strany(okrsky,data):
    vyber=['Voličiv seznamu','Vydanéobálky','Platnéhlasy']
    tabulka_s_cisly=[]
    finalni_strany=[]
    for okrsek in okrsky:
        if type(okrsek)==list:
            slovnik={}
            for cast in okrsek:
                strany=[]
                r2=requests.get(cast)
                stranka=bs4.BeautifulSoup(r2.text,'html.parser')
                vyber_id=filtrace(stranka)[0]
                vyber_headers=filtrace(stranka)[1]
                
                upravene_cislo=premena_na_cislo(vyber_headers)
                
                for i in stranka.find_all('td',{'class':'overflow_name'}):
                     strany.append(i.text)
            
                for i in range(len(vyber_id)):
                    for j in vyber:
                        if vyber_id[i]==j:
                            if j not in slovnik:
                                slovnik[j]=int(upravene_cislo[i])
                            else:
                                slovnik[j]+=int(upravene_cislo[i])
            
            finalni_strany.append(list(set(strany)))
        
                  
        else:
            strany=[]
            slovnik={}
            r2=requests.get(okrsek)
            stranka=bs4.BeautifulSoup(r2.text,'html.parser')
            vyber_id=filtrace(stranka)[0]
            vyber_headers=filtrace(stranka)[1]
                            
            upravene_cislo=premena_na_cislo(vyber_headers)
            
            for i in stranka.select('td.overflow_name'):
                strany.append(i.text)
            finalni_strany.append(strany)
            
            for i in range(len(vyber_id)):
                for j in vyber:
                    if vyber_id[i]==j:
                        if j not in slovnik:
                            slovnik[j]=int(upravene_cislo[i])
                            
        jednotliva_cisla=[]
        for i in slovnik.values():  
            jednotliva_cisla.append(i)
        tabulka_s_cisly.append(jednotliva_cisla)

    return tabulka_s_cisly,finalni_strany 

def souhrnna_tabulka(kod,nazev,cisla,strany):
    delka=[]
    for i in nazev:
        delka.append(len(i))
    nej=max(delka)
    hlavicka=['{: >}'.format('Kod obce'),'{0: <{1}}'.format('Nazev obce',nej),'{}'.format('Volici v seznamu'),
              '{}'.format('Vydane obalky'),'{: <}'.format('Platne hlasy'),'{: <}'.format('Kandidujici strany')]
    obsah=[]
    for i in range(len(kod)):
        tabulka=[]
        tabulka.append('{: >}'.format(kod[i])) 
        tabulka.append('{: <{}}'.format(nazev[i],nej)) 
        for k in range(3):
            tabulka.append(cisla[i][k])
        strana=', '.join(strany[i])
        tabulka.append('{: <}'.format(strana))
        obsah.append(tabulka)
    
    obsah_pd=pd.DataFrame(obsah,columns=hlavicka)
    return hlavicka, obsah

def zapis_do_souboru(hlavicka,obsah,soubor):
    print(f'Ukladam do souboru: {soubor}')
    with open(soubor,'w',newline='') as f:
        s=csv.writer(f)
        s.writerow(hlavicka)
        s.writerows(obsah)
       

web="https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4203"


if __name__=='__main__':
    main()

