
### IMPORTS SECTION

import streamlit as st
import requests
import time
import pandas as pd
from io import BytesIO
import numpy as np

st.set_page_config(
    page_title='Comparinator',
    page_icon='https://i.pinimg.com/564x/7b/87/3c/7b873c21da94ab660be4590250c8fb86.jpg', # This is an emoji shortcode. Could be a URL too.
)


### FUNCTIONS SECTION

def add_row_to_df(row, df):
    return pd.concat([df, row], ignore_index=True)

def remove_row_from_df(index, df):
    if index in df.index:
        df = df.drop(index)
        df.reset_index(drop=True, inplace=True)  # Reset index to keep it sequential
    return df

def get_card_details(card_name):
    url = f"https://api.scryfall.com/cards/named"
    params = {'fuzzy': card_name}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        card_data = response.json()
        return card_data
    else:
        return f"An error occurred: {response.status_code}"
    

def get_multiple_cards(card_names):
    cards_details = []
    for card_name in card_names:
        card_details = get_card_details(card_name)
        if isinstance(card_details, dict):
            cards_details.append(card_details)
        time.sleep(0.1)  # Add delay to respect rate limits
    return cards_details

def clean_card_deets(card_list):
    cards_details = get_multiple_cards(card_list)
    card_df = pd.DataFrame(cards_details)
    card_df['usd_price'] = card_df['prices'].apply(lambda x: x.get('usd', 'N/A'))
    output_card_df = card_df[['name', 'type_line', 'mana_cost', 
                          'cmc', 'oracle_text', 'usd_price', 
                          'power', 'toughness','released_at', 'image_uris']]
    output_card_df['cmc'] = output_card_df['cmc'].astype('int32')
    output_card_df['usd_price'] = output_card_df['usd_price'].astype('float64')
    output_card_df['released_at'] = pd.to_datetime(output_card_df['released_at'])
    
    return output_card_df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()


def kept_card_deets(card_names):

    card_df = pd.DataFrame(get_multiple_cards(card_names))
    card_df['usd_price'] = card_df['prices'].apply(lambda x: x.get('usd', 'N/A'))

    output_card_df = card_df[['name', 'type_line', 'mana_cost', 
                            'cmc', 'oracle_text', 'usd_price', 
                            'power', 'toughness','released_at']]
    output_card_df['cmc'] = output_card_df['cmc'].astype('int32')
    output_card_df['usd_price'] = output_card_df['usd_price'].astype('float64')
    output_card_df['released_at'] = pd.to_datetime(output_card_df['released_at'])

    return output_card_df


### BEGINNING STREAMLIT SETUP SECTION
st.title("Card Comparison for Deck Building")



### INPUT EXCEL SHEET SECTION

# check if the file has been uploaded before
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# create a placeholder for the file uploader
uploader_placeholder = st.empty()

# create a placeholder for containers
placeholder = st.empty()


if st.session_state.uploaded_file is None:
    # add initial content to the container
    with placeholder.container():

        cols = st.columns(5)
        col1, col2, col3, col4, col5 = cols

        # normal image urls
        col1.image('https://cards.scryfall.io/normal/front/b/f/bf1ef8ec-d915-41f2-b087-3d6d82e3db85.jpg?1591319833', use_column_width=True) # Akroma, Angel of Wrath
        col2.image('https://cards.scryfall.io/normal/front/f/1/f1fdb9bb-09a2-4ff7-bcd4-35ea33c1b752.jpg?1676452620', use_column_width=True) # Icebreaker Kraken
        col3.image('https://cards.scryfall.io/normal/front/5/7/57fab4fc-c8de-47ef-a717-3adb58c2f5b6.jpg?1562460627', use_column_width=True) # Demon of Death's Gate




        with col3:
            uploaded_file = uploader_placeholder.file_uploader("Upload an Excel file with 2 columns, \'considering\' and \'current\'", type="xlsx")
            if uploaded_file:
                st.session_state.uploaded_file = uploaded_file
                # read the excel file 
                df = pd.read_excel(st.session_state.uploaded_file)
                # clear the placeholder once a file is uploaded
                uploader_placeholder.empty()
                consider_list = [x for x in df['considering'] if pd.notna(x)]
                current_list = [x for x in df['current'] if pd.notna(x)]
            
            if st.button("Use Demo Data", use_container_width=True):
                consider_list = ['Beast Whisperer', 'Branch of Vitu-Ghazi', 'Experiment Twelve']
                current_list = ['Mystic Forge', 'Nervous Gardener', 'Panoptic Projektor', 'Primordial Mist', 'Printlifter Ooze', 'Rampant Growth']
                uploader_placeholder.empty()
                st.session_state.uploaded_file = 'demo'

                ### CREATE DATAFRAMES SECTION

                if 'consider_df' not in st.session_state:
                    # create an initial empty DataFrame
                    st.session_state.consider_df = clean_card_deets(consider_list)

                if 'current_df' not in st.session_state:
                    # create an initial empty DataFrame
                    st.session_state.current_df = clean_card_deets(current_list)


                if 'DMTC_df' not in st.session_state:
                    # create an initial empty DMTC DataFrame with columns
                    st.session_state.DMTC_df = pd.DataFrame(columns=[
                        'name', 'type_line', 'mana_cost', 'cmc', 'oracle_text', 
                        'usd_price', 'power', 'toughness', 'released_at', 'image_uris'])
                placeholder.empty()
                st.rerun()

        # normal image urls
        col4.image('https://cards.scryfall.io/normal/front/c/9/c93dd6cc-53e8-4c67-8838-180b19f02088.jpg?1689997653', use_column_width=True) # Avatar of Slaughter
        col5.image('https://cards.scryfall.io/normal/front/b/9/b9f1dbdc-e590-48a4-bc52-e9e4e907fb82.jpg?1690003248', use_column_width=True) # Nyxborn Behemoth




else:
    if len(st.session_state.consider_df) > 0:
        with placeholder.container():
            ### COMPARISON SECTION

            # create session state for loss counter
            if 'loss_count' not in st.session_state:
                st.session_state.loss_count = 0

            # create session state for the image index
            if 'current_card_index' not in st.session_state:
                st.session_state.current_card_index = 0

            # layout with two columns
            col1, col2 = st.columns([1, 1])

            with col1:
                st.write("Considering List")
                # display current image from the list
                st.image(st.session_state.consider_df.image_uris[0]['normal'], caption=f"{len(st.session_state.consider_df)} remaining in list")
                st.write(f"USD Price: ${st.session_state.consider_df['usd_price'][0]}")
                if st.button(st.session_state.consider_df['name'][0], use_container_width=True):
                    # add consider_df[0] to current_df
                    st.session_state.current_df = add_row_to_df(st.session_state.consider_df[:1], st.session_state.current_df)
                    # add current_df[st.session_state.current_card_index] to consider_df
                    st.session_state.consider_df = add_row_to_df(st.session_state.current_df[st.session_state.current_card_index:st.session_state.current_card_index+1:], st.session_state.consider_df)
                    # remove current_df[st.session_state.current_card_index] from current_df
                    # remove consider_df[0] from consider_df
                    st.session_state.consider_df = remove_row_from_df(0, st.session_state.consider_df)
                    st.session_state.current_df = remove_row_from_df(st.session_state.current_card_index, st.session_state.current_df)
                    st.session_state.loss_count = 0
                    st.rerun()  #rerun the script to update the image
                if st.button('Cut Card Now', use_container_width=True):
                    # add left card to DMTC_df
                    st.session_state.DMTC_df = add_row_to_df(st.session_state.consider_df[:1], st.session_state.DMTC_df)
                    # remove left card from consider_df
                    st.session_state.consider_df = remove_row_from_df(0, st.session_state.consider_df)
                    st.rerun()  #rerun the script to update the image
            
            with col2:
                st.write("Current List")
                st.image(st.session_state.current_df.image_uris[st.session_state.current_card_index]['normal'], caption=f"{st.session_state.current_card_index+1}/{len(st.session_state.current_df)}")
                st.write(f"USD Price: ${st.session_state.current_df['usd_price'][st.session_state.current_card_index]}")

                if st.button(st.session_state.current_df['name'][st.session_state.current_card_index], use_container_width=True):
                    # add one to loss count
                    st.session_state.loss_count += 1

                    # check to see if loss count is larger than length of current_df, meaning left card has gone through each one
                    if st.session_state.loss_count >= len(st.session_state.current_df):
                        # add left card to DMTC_df
                        st.session_state.DMTC_df = add_row_to_df(st.session_state.consider_df[:1], st.session_state.DMTC_df)
                        # remove left card from consider_df
                        st.session_state.consider_df = remove_row_from_df(0, st.session_state.consider_df)
                        # reset loss count
                        st.session_state.loss_count = 0
                        st.rerun()  #rerun the script to update the image
                    else:
                        # If not, increase index number to move through current_df
                        st.session_state.current_card_index = (st.session_state.current_card_index + 1) % len(st.session_state.current_df)
                        st.rerun()  #rerun the script to update the image
    elif len(st.session_state.consider_df) == 0 and len(st.session_state.DMTC_df) > 0:
               ### OUTPUT EXCEL SECTION
        placeholder.empty()
        with placeholder.container():
            # determine the lengths of the columns
            len_cut = len(st.session_state.DMTC_df['name'])
            len_kept = len(st.session_state.current_df['name'])
            max_len = max(len_cut, len_kept)

            # create new columns, padding the shorter one with NaN
            cut_column = st.session_state.DMTC_df['name'].tolist() + [np.nan] * (max_len - len_cut)
            kept_column = st.session_state.current_df['name'].tolist() + [np.nan] * (max_len - len_kept)
            kept_list = st.session_state.current_df['name'].tolist()

            detailed_kept_df = to_excel(kept_card_deets(kept_list))

            cut_kept_excel_data = to_excel(pd.DataFrame({'cut_cards': cut_column,'kept_cards': kept_column}))
            st.write("")
            st.write("")
            st.write("")

            st.write('All cards sorted. Click to download results.')
            # layout with two columns
            col1, col2 = st.columns([1, 1])
            

            with col1: 
                st.download_button(
                    label='Cut & Kept Cards',
                    data=cut_kept_excel_data,
                    file_name='cut_kept_results.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True)
            with col2:
                st.download_button(
                    label='Detailed Kept Cards',
                    data=detailed_kept_df,
                    file_name='detailed_kept_results.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                    use_container_width=True)

    else:
        st.write('Something went wrong - restart page and try again')

 

    






