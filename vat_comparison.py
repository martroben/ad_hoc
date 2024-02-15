# Compare the VAT collected in Estonia between 2022 and 2023, adjusted by local CPI to get the effect on consumption.
import plotly
from plotly.subplots import make_subplots

# Sources:
ee_vat_collected_reference = 'https://public.tableau.com/app/profile/rahandusministeerium.fpo/viz/Maksulaekumine2023/Esitlus'
ee_cpi_reference = 'https://www.inflation.eu/en/inflation-rates/estonia/historic-inflation/cpi-inflation-estonia-2023.aspx'

vat_monthly_2022_eur = [
    231432442,
    221109791,
    270880742,
    256942763,
    281232196,
    290345187,
    286783197,
    290996406,
    278730363,
    278661136,
    286053664,
    335642138
]

vat_monthly_2023_eur = [
    246207779,
    256028131,
    290985881,
    271595136,
    300069297,
    307081152,
    285461595,
    287576904,
    281300753,
    300397535,
    299555405,
    350160285
]

yearly_cpi_2023 = [
    0.1861,
    0.1755,
    0.1528,
    0.1347,
    0.1131,
    0.0919,
    0.0642,
    0.0460,
    0.0423,
    0.0492,
    0.0403,
    0.0403
]

vat_monthly_2022_cpi_adjusted_eur = [vat * (1 + cpi) for vat, cpi in zip(vat_monthly_2022_eur, yearly_cpi_2023)]
cumulative_difference = [sum(vat_monthly_2023_eur[i] - vat_monthly_2022_cpi_adjusted_eur[i] for i in range(5, j+1)) for j in range(6, 12)]


# Months
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Create traces
vat_2022_trace = plotly.graph_objects.Bar(
    x=months,
    y=vat_monthly_2022_cpi_adjusted_eur,
    name='2022 monthly VAT (CPI adjusted) eur',
    marker=dict(color='rgb(92, 131, 116)')
)

vat_2023_trace = plotly.graph_objects.Bar(
    x=months,
    y=vat_monthly_2023_eur,
    name='2023 monthly VAT eur',
    marker=dict(color='rgb(27, 66, 66)')
)

difference_trace = plotly.graph_objects.Scatter(
    x=months[6:],
    y=cumulative_difference,
    mode='lines',
    name='H2 cumulative difference (2023-2022) eur',
    line=dict(color='rgb(9, 38, 53)', width=1.5)
)

references_text = f'<b>References</b>:<br>VAT: {ee_vat_collected_reference}<br>CPI: {ee_cpi_reference}'

# Create subplot
fig = make_subplots(
    rows=2,
    cols=1,
    row_heights=[40, 5],
    shared_xaxes=True,
    vertical_spacing=0.05)

# Add bar traces to the first subplot
fig.add_trace(vat_2022_trace, row=1, col=1)
fig.add_trace(vat_2023_trace, row=1, col=1)

# Add line trace to the second subplot
fig.add_trace(difference_trace, row=2, col=1)

# Add label for December of the cumulative graph
fig.add_trace(plotly.graph_objects.Scatter(
    x=['Dec'],
    y=[cumulative_difference[-1]],
    mode='text',
    text=[f'{round(cumulative_difference[-1]/1e6)} M'],
    textposition='top right',
    showlegend=False
), row=2, col=1)

# Update layout
fig.update_layout(
    title='Monthly VAT Collected in Estonia (2022 vs 2023)',
    legend=dict(x=0.05, y=1.03, bgcolor='rgba(255, 255, 255, 0)', bordercolor='rgba(255, 255, 255, 0)'),
    plot_bgcolor='rgba(255, 255, 255, 1)',
    yaxis_gridcolor='rgba(211, 211, 211, 0.5)',
    barmode='group',
    annotations=[
        dict(
            x=0.05,
            y=-0.13,
            xref='paper',
            yref='paper',
            text=references_text,
            showarrow=False,
            bgcolor='rgba(255, 255, 255, 0)',
            align='left'
        )
    ],
    height=800,
    width=1000,
    yaxis1_tickfont_size=10,
    yaxis2_tickfont_size=8.5,
)

# Save the figure as a PNG file
fig.write_image("monthly_vat_estonia.png")
