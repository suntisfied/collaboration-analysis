from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import seaborn as sns
import matplotlib.colors as mcolors

def initialize_self_score_app(dash_app, dataset):
    @dash_app.callback(
        Output('self-meeting-dropdown', 'options'),
        Input('self-view-type-radio', 'value')
    )
    def set_self_meeting_options(view_type):
        meetings = dataset['meeting_number'].unique()
        return [{'label': f'Meeting {i}', 'value': i} for i in meetings]

    @dash_app.callback(
        Output('self-speaker-dropdown', 'options'),
        [Input('self-meeting-dropdown', 'value'),
         Input('self-view-type-radio', 'value')]
    )
    def set_self_speaker_options(selected_meeting, view_type):
        if not selected_meeting:
            speakers = dataset['speaker_number'].unique()
        else:
            filtered_df = dataset[dataset['meeting_number'].isin(selected_meeting)]
            speakers = filtered_df['speaker_number'].unique()
        return [{'label': f'Speaker {i}', 'value': i} for i in speakers]

    @dash_app.callback(
        [Output('self-meeting-dropdown', 'value'),
         Output('self-speaker-dropdown', 'value')],
        Input('self-reset-button', 'n_clicks')
    )
    def reset_self_filters(n_clicks):
        return None, None

    @dash_app.callback(
        Output('self-score-graph', 'figure'),
        [Input('self-meeting-dropdown', 'value'),
         Input('self-speaker-dropdown', 'value'),
         Input('self-view-type-radio', 'value')]
    )
    def update_self_score_graph(selected_meeting, selected_speakers, view_type):
        filtered_df = dataset[dataset['individual_collaboration_score'] != -1]
        filtered_df = filtered_df[filtered_df['overall_collaboration_score'] != -1]

        if selected_meeting:
            filtered_df = filtered_df[filtered_df['meeting_number'].isin(selected_meeting)]
        if selected_speakers:
            filtered_df = filtered_df[filtered_df['speaker_number'].isin(selected_speakers)]

        fig = go.Figure()

        if view_type == 'total':
            self_scores = filtered_df[filtered_df['speaker_id'] == filtered_df['next_speaker_id']].groupby('meeting_number')['individual_collaboration_score'].agg(['mean', 'sem']).reset_index()
            fig.add_trace(go.Scatter(
                x=self_scores['meeting_number'],
                y=self_scores['mean'],
                mode='lines+markers',
                name='Mean Individual Collaboration Score (Self)',
                line=dict(color='green'),
                marker=dict(color='green')
            ))
            fig.add_trace(go.Scatter(
                x=self_scores['meeting_number'],
                y=self_scores['mean'],
                mode='markers',
                marker=dict(size=8, color='green'),
                error_y=dict(
                    type='data',
                    array=self_scores['sem'],
                    visible=True
                ),
                showlegend=False
            ))

        else:  # view_type == 'by_speakers'
            self_scores_by_speaker = filtered_df[filtered_df['speaker_id'] == filtered_df['next_speaker_id']].groupby(['meeting_number', 'speaker_number'])['individual_collaboration_score'].agg(['mean', 'sem']).reset_index()
            palette = sns.color_palette('tab10', n_colors=self_scores_by_speaker['speaker_number'].nunique())
            color_map = {speaker: mcolors.rgb2hex(palette[i % len(palette)]) for i, speaker in enumerate(self_scores_by_speaker['speaker_number'].unique())}

            for speaker in self_scores_by_speaker['speaker_number'].unique():
                speaker_data = self_scores_by_speaker[self_scores_by_speaker['speaker_number'] == speaker]
                color = color_map[speaker]
                fig.add_trace(go.Scatter(
                    x=speaker_data['meeting_number'],
                    y=speaker_data['mean'],
                    mode='lines+markers',
                    name=f'Speaker {speaker}',
                    line=dict(color=color),
                    marker=dict(color=color),
                    error_y=dict(
                        type='data',
                        array=speaker_data['sem'],
                        visible=True
                    )
                ))

        fig.update_layout(
            title='Mean Individual Collaboration Score (Self) by Meeting',
            xaxis_title='Meeting Number',
            yaxis_title='Mean Individual Collaboration Score (Self)',
            xaxis=dict(tickmode='array', tickvals=filtered_df['meeting_number'].unique()),
            showlegend=True
        )

        # Bar plot for selected meetings
        if selected_meeting:
            bar_data = filtered_df[filtered_df['meeting_number'].isin(selected_meeting)]
            if not bar_data.empty:
                bar_data_agg = bar_data[bar_data['speaker_id'] == bar_data['next_speaker_id']].groupby('speaker_number')['individual_collaboration_score'].mean().reset_index()
                fig = go.Figure(data=[go.Bar(
                    x=bar_data_agg['speaker_number'],
                    y=bar_data_agg['individual_collaboration_score'],
                    marker_color=[color_map[speaker] for speaker in bar_data_agg['speaker_number']]
                )])
                fig.update_layout(
                    title='Mean Individual Collaboration Score (Self) by Speaker for Selected Meetings',
                    xaxis_title='Speaker Number',
                    yaxis_title='Individual Collaboration Score (Self)',
                    showlegend=False
                )

        return fig