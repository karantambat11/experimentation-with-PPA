import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt


# Define template headers
company_template_cols = [
    "SKU", "Pack Size", "Price", "Number of Washes",
    "Classification", "Price Tier", "Parent Brand",
    "Previous Volume", "Present Volume", "Previous Net Sales", "Present Net Sales", "Shelf Row"
]

competitor_template_cols = [
    "SKU", "Pack Size", "Price", "Number of Washes",
    "Classification", "Price Tier", "Parent Brand",
    "Previous Volume", "Present Volume", "Previous Net Sales", "Present Net Sales", "Shelf Row"
]

def generate_excel_download(df: pd.DataFrame):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Template")
    buffer.seek(0)
    return buffer

# --- UI Starts ---
st.title("📦 Price Pack Architecture Tool")

st.markdown("Before uploading, please use the templates below to prepare your data:")

col1, col2 = st.columns(2)

with col1:
    company_buffer = generate_excel_download(pd.DataFrame(columns=company_template_cols))
    st.download_button(
        label="📥 Download Company Template",
        data=company_buffer,
        file_name="company_data_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col2:
    competitor_buffer = generate_excel_download(pd.DataFrame(columns=competitor_template_cols))
    st.download_button(
        label="📥 Download Competitor Template",
        data=competitor_buffer,
        file_name="competitor_data_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




st.header("Upload Your Data")
company_file = st.file_uploader("Upload Your Company Data (CSV)", type="csv")
competitor_file = st.file_uploader("Upload Competitor Data (CSV)", type="csv")

company_cols = ["SKU", "Pack Size", "Price", "Number of Washes", 
                "Classification", "Price Tier", "Parent Brand", 
                "Previous Volume", "Present Volume", 
                "Previous Net Sales", "Present Net Sales"]

competitor_cols = ["SKU", "Pack Size", "Price", "Number of Washes", 
                   "Classification", "Price Tier", "Parent Brand"]

def assign_tier(ppw, thresholds):
    if ppw <= thresholds['Value'][1]:
        return 'Value'
    elif ppw <= thresholds['Mainstream'][1]:
        return 'Mainstream'
    elif ppw <= thresholds['Premium'][1]:
        return 'Premium'
    else:
        return 'Others'

# ✅ Moved outside assign_tier()
def generate_dynamic_html(sku_matrix, classification_metrics, tier_metrics, classifications, tiers):
    html = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: 13px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 10px 12px; /* Increased padding */
            text-align: center;
            vertical-align: middle;
        }
        th {
            font-weight: bold;
        }
        td[colspan="3"] {
            min-width: 180px; /* Adjust to fit 20 characters easily */
        }
    </style>


    <table>
        <tr>
            <th>Classification</th>
    """
    for cls in classifications:
        html += f'<th colspan="3">{cls}</th>'
    html += '<th rowspan="3">Avg PP CPW</th>'
    html += '<th rowspan="3">Value Weight</th>'
    html += '<th rowspan="3">Growth</th></tr>'

    html += "<tr><td>Net Sales Growth %</td>"
    for cls in classifications:
        html += f'<td colspan="3">{classification_metrics[cls]["Growth"]}</td>'
    html += '</tr>'

    html += "<tr><td>Value Share %</td>"
    for cls in classifications:
        html += f'<td colspan="3">{classification_metrics[cls]["Value"]}</td>'
    html += '</tr>'

    html += "<tr><td>PPW Range</td>"
    for cls in classifications:
        html += f'<td colspan="3">{classification_metrics[cls]["PPW"]}</td>'
    html += '<td></td><td></td><td></td></tr>'

    for tier in tiers:
        html += f'<tr><td>{tier}</td>'
        for cls in classifications:
            skus = sku_matrix[tier][cls]
            html += f'<td colspan="3">{"<br>".join(skus) if skus else "-"}</td>'
        html += f'<td>{tier_metrics[tier]["PPW"]}</td>'
        html += f'<td>{tier_metrics[tier]["Share"]}</td>'
        html += f'<td>{tier_metrics[tier]["Growth"]}</td></tr>'
    html += "</table>"
    return html





if 'classified' not in st.session_state:
    st.session_state.classified = False


if company_file and competitor_file:
    st.subheader("Shelf Configuration")
    shelf_rows = st.number_input("Enter number of shelf rows:", min_value=1, value=3)
    effective_sku_capacity = shelf_rows * 3 * 0.75
    st.markdown(f"**Effective SKU Capacity (3 SKUs/row × 0.75):** {effective_sku_capacity:.1f}")

    st.subheader("Currency Settings")
    currency_symbol = st.text_input("Enter your currency symbol (e.g. ₹, $, €, etc.):", value="₹")
    company_df = pd.read_csv(company_file)
    competitor_df = pd.read_csv(competitor_file)

    if company_df["Classification"].nunique() > 4:
        st.error("You have more than 4 classifications in your company data.")
    else:
                # Clean numeric fields
                # Clean numeric columns (company)
        company_numeric_cols = [
            "Price", "Number of Washes", "Previous Volume", "Present Volume", 
            "Previous Net Sales", "Present Net Sales", "Shelf Row"
        ]
        company_df[company_numeric_cols] = company_df[company_numeric_cols].apply(pd.to_numeric, errors="coerce")
        
        # Clean numeric columns (competitor)
        competitor_numeric_cols = ["Price", "Number of Washes", "Previous Volume", "Present Volume", "Previous Net Sales", "Present Net Sales", "Shelf Row"]
        competitor_df[competitor_numeric_cols] = competitor_df[competitor_numeric_cols].apply(pd.to_numeric, errors="coerce")


        
        # Calculate Price per Wash
        company_df["Price per Wash"] = company_df["Price"] / company_df["Number of Washes"]
                # Filter for valid SKUs (for growth only)
        valid_company_df = company_df[
            ~((company_df['Previous Volume'].fillna(0) == 0) & (company_df['Previous Net Sales'].fillna(0) == 0))
        ].copy()

        competitor_df["Price per Wash"] = competitor_df["Price"] / competitor_df["Number of Washes"]


        st.subheader("Price per Wash Range")
        st.write(f"Company: {currency_symbol}{company_df['Price per Wash'].min():.2f} – {currency_symbol}{company_df['Price per Wash'].max():.2f}")
        st.write(f"Competitor: {currency_symbol}{competitor_df['Price per Wash'].min():.2f} – {currency_symbol}{competitor_df['Price per Wash'].max():.2f}")
        
        st.subheader(f"Set Price Tier Thresholds ({currency_symbol})")
        with st.form("thresholds"):
            col1, col2, col3 = st.columns(3)
            with col1:
                value_max = st.number_input(f"Value: Max {currency_symbol}", value=.13)
            with col2:
                mainstream_max = st.number_input(f"Mainstream: Max {currency_symbol}", value=.17)
            with col3:
                premium_max = st.number_input(f"Premium: Max {currency_symbol}", value=1)
            submit_btn = st.form_submit_button("Classify SKUs")
            if submit_btn:
                st.session_state['classified'] = True



        if submit_btn:
            st.session_state['classified'] = True  # 🔒 Locks the view to analysis mode
            st.rerun()  # 🔁 Reruns the app to jump into analysis block
    
        if st.session_state['classified']:
            thresholds = {
                'Value': (0.0, value_max),
                'Mainstream': (value_max, mainstream_max),
                'Premium': (mainstream_max, premium_max)
            }
   


            company_df['Calculated Price Tier'] = company_df["Price per Wash"].apply(lambda x: assign_tier(x, thresholds))
            competitor_df['Calculated Price Tier'] = competitor_df["Price per Wash"].apply(lambda x: assign_tier(x, thresholds))
            company_df['Is Competitor'] = False
            competitor_df['Is Competitor'] = True

            full_df = pd.concat([company_df, competitor_df], ignore_index=True)
# ----- ✅ Corrected Metrics Calculation -----

            tiers = ['Premium', 'Mainstream', 'Value']
            classifications = sorted(full_df['Classification'].unique())
            
            sku_matrix = {tier: {cls: [] for cls in classifications} for tier in tiers}
            classification_metrics = {}
            tier_metrics = {}
            
            total_present_sales = full_df['Present Net Sales'].sum()
            
            # --- Classification-level metrics
            for cls in classifications:
                cls_df = full_df[full_df['Classification'] == cls]
                prev_rev = valid_company_df[valid_company_df['Classification'] == cls]['Previous Net Sales'].sum()
                curr_rev = cls_df['Present Net Sales'].sum()
                
                growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
                share = (curr_rev / total_present_sales * 100) if total_present_sales else 0
                ppw_range = f"{cls_df['Price per Wash'].min():.2f} – {cls_df['Price per Wash'].max():.2f}" if not cls_df.empty else "-"
                
                classification_metrics[cls] = {
                    "Growth": f"{growth:.1f}%",
                    "Value": f"{share:.1f}%",
                    "PPW": ppw_range
                }
            
            # --- Tier-level metrics
            for tier in tiers:
                tier_df = full_df[full_df["Calculated Price Tier"] == tier]
                prev_rev = valid_company_df[valid_company_df["Calculated Price Tier"] == tier]["Previous Net Sales"].sum()
                curr_rev = tier_df["Present Net Sales"].sum()
                
                growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
                share = (curr_rev / total_present_sales * 100) if total_present_sales else 0
                
                min_ppw = tier_df["Price per Wash"].min()
                max_ppw = tier_df["Price per Wash"].max()
                ppw_range = f"{currency_symbol}{min_ppw:.2f} – {currency_symbol}{max_ppw:.2f}" if not tier_df.empty else "-"
                
                tier_metrics[tier] = {
                    "PPW": ppw_range,
                    "Growth": f"{growth:.1f}%",
                    "Share": f"{share:.1f}%"
                }
            
            # --- Also rebuild SKU matrix (this is fine, no change needed)
            for _, row in company_df.iterrows():

                tier = row["Calculated Price Tier"]
                cls = row["Classification"]
                sku = row["SKU"]
                if tier in sku_matrix and cls in sku_matrix[tier]:
                    sku_matrix[tier][cls].append(sku)


            # After HTML render
            # Store dynamic HTML once on submit
           # Always regenerate and show latest updated matrix (no cache)
            dynamic_html = generate_dynamic_html(sku_matrix, classification_metrics, tier_metrics, classifications, tiers)
            st.markdown(dynamic_html, unsafe_allow_html=True)



          # ----- SKU GROWTH SUMMARY -----
            st.subheader("📈 SKU-Level Growth Summary (Our Company Only)")
            
            sku_growth_summary = []
            
            for _, row in company_df.iterrows():
                sku = row['SKU']
                prev_vol = row['Previous Volume']
                curr_vol = row['Present Volume']
                prev_rev = row['Previous Net Sales']
                curr_rev = row['Present Net Sales']
            
                volume_growth = ((curr_vol - prev_vol) / prev_vol * 100) if prev_vol else 0
                Net_Sales_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
            
                sku_growth_summary.append({
                    "SKU": sku,
                    "Previous Volume": prev_vol,
                    "Present Volume": curr_vol,
                    "Volume Growth %": f"{volume_growth:.1f}%",
                    "Previous Net Sales": prev_rev,
                    "Present Net Sales": curr_rev,
                    "Net Sales Growth %": f"{Net_Sales_growth:.1f}%"
                })
            
            # Show as table
            st.dataframe(pd.DataFrame(sku_growth_summary))


          # SCATTER PLOT: Retail Price vs. Price Per Wash
            from adjustText import adjust_text
            import numpy as np
            
            st.subheader("📈 Scatter Plot: Retail Price vs. Price Per Wash")
            
            # Combine company and competitor for plot
            plot_df = pd.concat([company_df, competitor_df], ignore_index=True).copy()
            
            # Add small jitter to overlapping points
            plot_df['Jittered PPW'] = plot_df['Price per Wash'] + np.random.normal(0, 0.002, size=len(plot_df))
            plot_df['Jittered Price'] = plot_df['Price'] + np.random.normal(0, 0.3, size=len(plot_df))
            
            # Define colors
            plot_df['Color'] = plot_df['Is Competitor'].apply(lambda x: 'green' if x else 'navy')
            
            # Axis ranges
            x_min = plot_df['Jittered PPW'].min() - 0.03
            x_max = plot_df['Jittered PPW'].max() + 0.03
            y_min = plot_df['Jittered Price'].min() - 2
            y_max = plot_df['Jittered Price'].max() + 2
            
            # Matplotlib Plot
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Plot each point with its color
            ax.scatter(plot_df['Jittered PPW'], plot_df['Jittered Price'], c=plot_df['Color'], s=70, alpha=0.8)
            
            # Add labels with adjustText
            texts = [
                ax.text(row['Jittered PPW'], row['Jittered Price'], row['SKU'], fontsize=8)
                for _, row in plot_df.iterrows()
            ]
            
            adjust_text(
                texts,
                ax=ax,
                arrowprops=dict(arrowstyle="-", color='gray', lw=0.5),
                expand_points=(1.2, 1.4),
                expand_text=(1.2, 1.4),
                force_text=0.5,
                force_points=0.4,
                only_move={'points': 'y', 'text': 'xy'},
            )
            
            ax.set_xlabel("Price Per Wash")
            ax.set_ylabel("Retail Price")
            ax.set_title("Scatter Plot of SKUs")
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.grid(True, linestyle='--', alpha=0.5)
            
            st.pyplot(fig)

            

            st.subheader("📊 API Comparison: Our SKUs vs Competitors (By Classification & Tier)")

            

            api_rows = []
            
            # Loop through all classification × tier segments
            for classification in classifications:
                for tier in tiers:
                    segment_df = full_df[
                        (full_df["Classification"] == classification) &
                        (full_df["Calculated Price Tier"] == tier)
                    ]
                    our_skus = segment_df[segment_df["Is Competitor"] == False]
                    comp_skus = segment_df[segment_df["Is Competitor"] == True]
            
                    if not comp_skus.empty:
                        avg_comp_ppw = comp_skus["Price per Wash"].mean()
            
                        for _, our_row in our_skus.iterrows():
                            our_ppw = our_row["Price per Wash"]
                            api = our_ppw / avg_comp_ppw if avg_comp_ppw else float('nan')
            
                            api_rows.append({
                                "Classification": classification,
                                "Price Tier": tier,
                                "Our SKU": our_row["SKU"],
                                "Our PPW": round(our_ppw, 2),
                                "Avg Competitor PPW": round(avg_comp_ppw, 2),
                                "API (Our / Comp)": round(api, 2)
                            })
            
            if api_rows:
                api_df = pd.DataFrame(api_rows)
                st.dataframe(api_df)
            else:
                st.info("No competitor SKUs found in any classification-tier segment.")

            
            if api_rows:
                api_df = pd.DataFrame(api_rows)
                st.dataframe(api_df)
            else:
                st.info("No matching competitor SKUs found in any classification-tier combination.")

            st.subheader("🔁 Compare API Between Two SKUs")
# Combine company and competitor for dropdowns
            sku_ppw_map = full_df.set_index("SKU")["Price per Wash"].to_dict()
            sku_list = sorted(sku_ppw_map.keys())
            
            col1, col2 = st.columns(2)
            with col1:
                sku_a = st.selectbox("Select SKU A", sku_list)
            with col2:
                sku_b = st.selectbox("Select SKU B", sku_list, index=1)
            
            if sku_a and sku_b and sku_a != sku_b:
                ppw_a = sku_ppw_map[sku_a]
                ppw_b = sku_ppw_map[sku_b]
            
                api = ppw_a / ppw_b if ppw_b else float('nan')
                
                st.markdown(f"""
                **SKU A:** `{sku_a}` — PPW = {currency_symbol}{ppw_a:.2f}  
                **SKU B:** `{sku_b}` — PPW = {currency_symbol}{ppw_b:.2f}  
                
                📊 **API (A vs B)** = {ppw_a:.2f} / {ppw_b:.2f} = **{api:.2f}**
                """)
            else:
                st.info("Please select two different SKUs.")

# --- 📊 New Section: Classification and Price Tier Growth and Share Analysis ---

            st.header("📊 Classification and Price Tier: Value Growth and Share")
            
            # Full dataset: company + competitor
            full_df_for_analysis = pd.concat([company_df, competitor_df], ignore_index=True)
            
            # --- 📂 1. Classification Level Analysis ---
            classification_summary = []
            
            total_prev_sales = full_df_for_analysis["Previous Net Sales"].sum()
            total_curr_sales = full_df_for_analysis["Present Net Sales"].sum()
            
            for cls in sorted(full_df_for_analysis["Classification"].unique()):
                cls_df = full_df_for_analysis[full_df_for_analysis["Classification"] == cls]
                
                prev_sales = cls_df["Previous Net Sales"].sum()
                curr_sales = cls_df["Present Net Sales"].sum()
                
                growth = ((curr_sales - prev_sales) / prev_sales * 100) if prev_sales else 0
                share = (curr_sales / total_curr_sales * 100) if total_curr_sales else 0
                
                classification_summary.append({
                    "Classification": cls,
                    "Sales Value Growth %": f"{growth:.1f}%",
                    "Value Share %": f"{share:.1f}%"
                })
            
            classification_df = pd.DataFrame(classification_summary)
            
            st.subheader("📂 Classification Summary")
            st.dataframe(classification_df)
            
            # --- 📂 2. Price Tier Level Analysis ---
            tier_summary = []
            
            for tier in ['Premium', 'Mainstream', 'Value']:  # Ensure order
                tier_df = full_df_for_analysis[full_df_for_analysis["Calculated Price Tier"] == tier]
                
                prev_sales = tier_df["Previous Net Sales"].sum()
                curr_sales = tier_df["Present Net Sales"].sum()
                
                growth = ((curr_sales - prev_sales) / prev_sales * 100) if prev_sales else 0
                share = (curr_sales / total_curr_sales * 100) if total_curr_sales else 0
                
                tier_summary.append({
                    "Price Tier": tier,
                    "Sales Value Growth %": f"{growth:.1f}%",
                    "Value Share %": f"{share:.1f}%"
                })
            
            tier_df_final = pd.DataFrame(tier_summary)
            
            st.subheader("📂 Price Tier Summary")
            st.dataframe(tier_df_final)


# --- 📊 New Section: Matrix of Price Tier × Classification ---

            # --- 📊 New Section: Refined Price Tier × Classification Matrix ---

            # --- 📊 New Section: Refined Price Tier × Classification Matrix (Horizontal Layout) ---

            st.header("📊 Price Tier vs Classification Matrix (Sales, Share %, Growth %) [Horizontal]")
            
            # Full data: company + competitor
            full_df_for_matrix = pd.concat([company_df, competitor_df], ignore_index=True)
            
            tiers = ['Premium', 'Mainstream', 'Value']  # Keep same order
            classifications = sorted(full_df_for_matrix['Classification'].unique())
            
            # Initialize matrix
            matrix_html = """
            <style>
                table.main {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                }
                table.main th, table.main td {
                    border: 1px solid #ddd;
                    padding: 6px;
                    text-align: center;
                    vertical-align: middle;
                }
                table.main th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                table.inner {
                    width: 100%;
                    border: none;
                }
                table.inner td {
                    border: none;
                    padding: 2px 5px;
                    font-size: 11px;
                    text-align: center;
                }
            </style>
            
            <table class="main">
            <tr>
                <th>Price Tier \\ Classification</th>
            """
            
            for cls in classifications:
                matrix_html += f"<th>{cls}</th>"
            matrix_html += "</tr>"
            
            for tier in tiers:
                matrix_html += f"<tr><td><b>{tier}</b></td>"
                for cls in classifications:
                    segment_df = full_df_for_matrix[
                        (full_df_for_matrix["Calculated Price Tier"] == tier) &
                        (full_df_for_matrix["Classification"] == cls)
                    ]
                    
                    if not segment_df.empty:
                        total_present = segment_df["Present Net Sales"].sum()
                        total_previous = segment_df["Previous Net Sales"].sum()
                        our_present = segment_df[segment_df["Is Competitor"] == False]["Present Net Sales"].sum()
            
                        share_percent = (our_present / total_present * 100) if total_present else 0
                        growth_percent = ((total_present - total_previous) / total_previous * 100) if total_previous else 0
            
                        # Mini table inside each cell (horizontal layout)
                        cell_text = f"""
                        <table class="inner">
                            <tr>
                                <td><b>{currency_symbol}{total_present:,.0f}</b></td>
                                <td>{share_percent:.1f}%</td>
                                <td>{growth_percent:.1f}%</td>
                            </tr>
                        </table>
                        """
                    else:
                        cell_text = "-"
            
                    matrix_html += f"<td>{cell_text}</td>"
                matrix_html += "</tr>"
            
            matrix_html += "</table>"
            
            st.markdown(matrix_html, unsafe_allow_html=True)


# --- 📊 Brand-Level Market Share and BPS Change Analysis ---

            st.header("🏷️ Brand Market Share and BPS Change")
            
            # Full dataset
            full_df_for_brands = pd.concat([company_df, competitor_df], ignore_index=True)
            
            total_previous_net_sales = full_df_for_brands["Previous Net Sales"].sum()
            total_present_net_sales = full_df_for_brands["Present Net Sales"].sum()
            
            brand_summary = []
            
            for brand in sorted(full_df_for_brands["Parent Brand"].dropna().unique()):
                brand_df = full_df_for_brands[full_df_for_brands["Parent Brand"] == brand]
                
                prev_sales = brand_df["Previous Net Sales"].sum()
                curr_sales = brand_df["Present Net Sales"].sum()
                
                prev_share = (prev_sales / total_previous_net_sales * 100) if total_previous_net_sales else 0
                curr_share = (curr_sales / total_present_net_sales * 100) if total_present_net_sales else 0
                bps_change = (curr_share - prev_share) * 100  # Basis Points
                
                brand_summary.append({
                    "Parent Brand": brand,
                    "Previous Share %": f"{prev_share:.1f}%",
                    "Current Share %": f"{curr_share:.1f}%",
                    "BPS Change": f"{bps_change:.0f} BPS"
                })
            
            brand_summary_df = pd.DataFrame(brand_summary).sort_values(by="Current Share %", ascending=False)
            
            st.dataframe(brand_summary_df)








            
