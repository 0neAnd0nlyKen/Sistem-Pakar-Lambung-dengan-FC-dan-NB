import streamlit as st
import pandas as pd
from db_funcs import init_connection, get_table_data

# Fungsi Naive Bayes
def naive_bayes_diagnosis(answers):
    cnx = init_connection()
    if cnx is None:
        st.error("Could not connect to database for diagnosis.")
        return None

    try:
        # 1. Fetch data_penyakit_table
        data_penyakit = get_table_data(cnx, 'data_penyakit_table')
        if data_penyakit.empty:
            st.error("Could not fetch 'data_penyakit_table' from database.")
            return None
        # Ensure consistent column names (lowercase) if not already
        data_penyakit.columns = [col.lower() for col in data_penyakit.columns]

        # 2. Fetch case_base_table
        case_base = get_table_data(cnx, 'case_base_table')
        if case_base.empty:
            st.error("Could not fetch 'case_base_table' from database.")
            return None
        # Ensure consistent column names (lowercase) if not already
        case_base.columns = [col.lower() if not col.startswith('G') else col for col in case_base.columns]

        # Map user answers to G-codes (0 or 1)
        input_gejala = {}
        gejala_codes = [f'G{i:02d}' for i in range(1, len(answers) + 1)] # Using len(answers) to match available questions
        for i, answer in enumerate(answers):
            if answer == 'Ya':
                input_gejala[gejala_codes[i]] = 1
            elif answer == 'Tidak':
                input_gejala[gejala_codes[i]] = 0
            # 'Tidak Diketahui' answers are not used in direct likelihood calculation for now

        # 3. Calculate Prior Probabilities
        prior = case_base['penyakit'].value_counts(normalize=True)

        # 4. Calculate Likelihoods with Laplace Smoothing
        likelihood = {}
        gejala_cols_in_case_base = [col for col in case_base.columns if col.startswith('G')]

        for penyakit_code in data_penyakit['kode_penyakit']:
            subset = case_base[case_base['penyakit'] == penyakit_code]
            total_cases_for_disease = len(subset)

            likelihood[penyakit_code] = {}

            for g_code in gejala_cols_in_case_base:
                if g_code in input_gejala: # Only calculate likelihood for symptoms in input_gejala
                    count_yes = subset[g_code].sum()

                    # Laplace smoothing
                    prob_yes = (count_yes + 1) / (total_cases_for_disease + 2)
                    prob_no = (total_cases_for_disease - count_yes + 1) / (total_cases_for_disease + 2)

                    likelihood[penyakit_code][g_code] = {
                        '1': prob_yes,
                        '0': prob_no
                    }
                # If g_code is not in input_gejala, it means the user marked it as 'Tidak Diketahui'
                # or it wasn't asked. We don't factor it into the likelihood product for that specific symptom.

        # 5. Implement Naive Bayes Algorithm
        disease_probabilities = {}
        total_probability_sum = 0

        for penyakit_code in data_penyakit['kode_penyakit']:
            prior_p = prior.get(penyakit_code, 1e-6) # Use a small value if prior is 0 for robustness
            probability_for_disease = prior_p

            # Multiply by likelihoods of the observed symptoms
            for g_code, val in input_gejala.items():
                if g_code in likelihood[penyakit_code]:
                    prob_g_given_d = likelihood[penyakit_code][g_code][str(val)]
                    probability_for_disease *= prob_g_given_d
                else:
                    # If a G-code from input_gejala is not found in likelihood (shouldn't happen if setup is correct),
                    # assign a neutral probability or handle as error.
                    # For now, we assume all relevant G-codes are in likelihood.
                    pass

            disease_probabilities[penyakit_code] = probability_for_disease
            total_probability_sum += probability_for_disease

        # 6. Normalize Probabilities
        normalized_probabilities = {}
        if total_probability_sum > 0:
            for pk_code, prob in disease_probabilities.items():
                normalized_probabilities[pk_code] = prob / total_probability_sum
        else:
            # If total_probability_sum is 0, assign equal probability (or handle as no diagnosis)
            num_diseases = len(data_penyakit['kode_penyakit'])
            for pk_code in data_penyakit['kode_penyakit']:
                normalized_probabilities[pk_code] = 1.0 / num_diseases if num_diseases > 0 else 0

        # 7. Determine the disease with the highest probability
        if not normalized_probabilities:
            return {
                'kode_penyakit': 'Unknown',
                'nama_penyakit': 'Tidak Dapat Didiagnosis',
                'confidence': 0.0,
                'gejala_terdeteksi': sum(1 for ans in answers if ans == 'Ya'),
                'total_gejala': len(answers)
            }

        most_likely_disease_code = max(normalized_probabilities, key=normalized_probabilities.get)
        confidence = normalized_probabilities[most_likely_disease_code]

        disease_name = data_penyakit.loc[data_penyakit['kode_penyakit'] == most_likely_disease_code, 'nama_penyakit'].values[0]

        # Return the result dictionary
        return {
            'kode_penyakit': most_likely_disease_code,
            'nama_penyakit': disease_name,
            'confidence': confidence,
            'gejala_terdeteksi': sum(1 for ans in answers if ans == 'Ya'),
            'total_gejala': len(answers)
        }
    except Exception as e:
        st.error(f"An error occurred during diagnosis: {e}")
        return None
