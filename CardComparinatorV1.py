# To run this in terminal, use:
# streamlit run CardComparinator.py --server.enableXsrfProtection false


### IMPORTS SECTION

import streamlit as st
import requests
import time
import pandas as pd
from io import BytesIO
import numpy as np



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


### BEGINNING STREAMLIT SETUP SECTION
st.title("Card Comparison for Deck Building")



### INPUT EXCEL SHEET SECTION

# check if the file has been uploaded before
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# create a placeholder for the file uploader
uploader_placeholder = st.empty()



# create a placeholder
placeholder = st.empty()


if st.session_state.uploaded_file is None:
    # add initial content to the placeholder
    with placeholder.container():
        uploaded_file = uploader_placeholder.file_uploader("Upload an Excel file", type="xlsx")
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            # read the excel file 
            df = pd.read_excel(st.session_state.uploaded_file)
            # clear the placeholder once a file is uploaded
            uploader_placeholder.empty()
            consider_list = [x for x in df['considering'] if pd.notna(x)]
            current_list = [x for x in df['current'] if pd.notna(x)]

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
                # display current image from the list
                st.image(st.session_state.consider_df.image_uris[0]['normal'], caption="Left Image")
                if st.button("Left Button"):
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
            
            with col2:
                st.image(st.session_state.current_df.image_uris[st.session_state.current_card_index]['normal'], caption="Right Image")
                if st.button("Right Button"):
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

            excel_data = to_excel(pd.DataFrame({'cut_cards': cut_column,'kept_cards': kept_column}))

            st.download_button(
                label='Download Excel File',
                data=excel_data,
                file_name='comparison_results.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.write('Something went wrong - restart page and try again')

 

    






