import csv
import plotly
import re
import requests

# Data source
google_sheets_doc_id = "1yRQxL9ZUJ9OTGiAhz7t7cAIk_GslfQkvWox16ivsqfQ"
data_url = f"https://docs.google.com/spreadsheets/d/{google_sheets_doc_id}/export?format=csv"

# Settings
plot_title = "Salaries of analysts"
x_axis_field = "Brutopalk"
x_axis_title = "Gross salary (eur)"
y_axis_field = "Kogemus valdkonnas"  # alternative: "Sinu vanus?"
y_axis_title = "Experience (years)"  # alternative: "Age (years)"
label_field = "Ametikoht"
colour_field = "Haridustase"

colour_field_eng_reference = {
    "not specified": "not specified",
    "põhi": "middle school",
    "kutse": "vocational",
    "kesk": "high school",
    "rakendus": "applied higher",
    "baka": "bachelors",
    "mag": "masters",
    "dok": "doctorate"}

# Download data
response = requests.get(data_url)
response.encoding = "utf8"
reader = csv.DictReader(response.iter_lines(decode_unicode=True))

# Filter data
filter_field = "Ametikoht"
filter_regex_pattern = r"anal"  # alternatives: developers: r"aren"  all: r""
filtered_records = [record for record in reader if re.search(filter_regex_pattern, record[filter_field], re.IGNORECASE)]

# Extract and clean data
x_data = [float(record[x_axis_field]) for record in filtered_records]
y_data_nulls_removed = [record[y_axis_field] or 0 for record in filtered_records]
y_data = [int(data_point) for data_point in y_data_nulls_removed]
label_data = [record[label_field] for record in filtered_records]
colour_field_map = {re.compile(key, re.IGNORECASE): value for key, value in colour_field_eng_reference.items()}
colour_data_raw = [record[colour_field] or "not specified" for record in filtered_records]
colour_data = [next(value for pattern, value in colour_field_map.items() if pattern.search(colour_data_point)) for colour_data_point in colour_data_raw]

# Map colours to values with maximum scale stretch
colour_scale_name = "RdBu"
colour_scale = plotly.colors.PLOTLY_SCALES[colour_scale_name]
existing_colours = [value for value in colour_field_eng_reference.values() if value in colour_data]
colour_map_positions = {value: existing_colours.index(value) / (len(existing_colours) - 1) for value in existing_colours}
colour_map = {key: colour_scale[int(value*(len(colour_scale)-1))][1] for key, value in colour_map_positions.items()}

# Main scatter plot
scatter_plot = plotly.graph_objects.Scatter(
    x=x_data,
    y=y_data,
    mode="markers",
    text=label_data,
    hoverinfo="text",
    marker=dict(color=[colour_map[data_point] for data_point in colour_data]),
    showlegend=False)

# Use separate scatter traces for each colour field category to get the colour legend
# (plotly peculiarity)
legend_traces = []
for category, color in colour_map.items():
    trace = plotly.graph_objects.Scatter(
        x=[None], y=[None],  # Invisible markers
        mode="markers",
        marker=dict(color=color),
        name=category)
    legend_traces.append(trace)

# Drop a fraction of top values for better visual
x_outliers = 0.015
x_cap = sorted(x_data)[int(len(x_data) * (1 - x_outliers))]

# Add plot labels and legend
figure = plotly.graph_objects.Figure(data=[scatter_plot] + legend_traces)
figure.update_layout(
    title=plot_title,
    xaxis=dict(
        title = x_axis_title,
        range = [min(x_data) - 100, x_cap + 100]),
    yaxis_title=y_axis_title)

# Show / save
figure.show()
# figure.write_image(f"{x_axis_field.lower().replace(' ', '_')}_vs_{y_axis_field.lower().replace(' ', '_')}_plot.png")
