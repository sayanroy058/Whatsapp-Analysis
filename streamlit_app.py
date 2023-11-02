import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import functions  # Your functions module

# Set the title of the Streamlit app
st.title('WhatsApp Chat Analyzer')

# Allow the user to upload a WhatsApp chat data file
file = st.file_uploader("Choose a WhatsApp chat data file")

if file:
    # Generate a DataFrame from the uploaded file using the functions module
    df = functions.generateDataFrame(file)
    
    try:
        # Ask the user to select the date format in the text file
        dayfirst = st.radio("Select Date Format in the text file:", ('dd-mm-yy', 'mm-dd-yy'))
        if dayfirst == 'dd-mm-yy':
            dayfirst = True
        else:
            dayfirst = False

        # Get the list of unique users from the chat data
        users = functions.getUsers(df)

        # Create a sidebar element for user selection
        users_s = st.sidebar.selectbox("Select User to View Analysis", users)
        selected_user = ""

        # Show analysis for the selected user when the button is pressed
        if st.sidebar.button("Show Analysis"):
            selected_user = users_s

            # Display the selected user for analysis
            st.title("Showing Results for: " + selected_user)

            # Preprocess the data and filter by user if not "Everyone"
            df = functions.PreProcess(df, dayfirst)
            if selected_user != "Everyone":
                df = df[df['User'] == selected_user]

            # Get various statistics about the chat data
            df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count = functions.getStats(df)

            # Display chat statistics
            st.title("Chat Statistics")
            stats_c = ["Total Messages", "Total Words", "Media Shared", "Links Shared", "Messages Deleted"]
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.subheader(stats_c[0])
                st.title(msg_count)
            with c2:
                st.subheader(stats_c[1])
                st.title(word_count)
            with c3:
                st.subheader(stats_c[2])
                st.title(media_cnt)
            with c4:
                st.subheader(stats_c[3])
                st.title(links_cnt)
            with c5:
                st.subheader(stats_c[4])
                st.title(deleted_msgs_cnt)

            # User Activity Count
            if selected_user == 'Everyone':
                x = df['User'].value_counts().head()
                name = x.index
                count = x.values
                st.title("Messaging Frequency")
                st.subheader('Messaging Percentage Count of Users')
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(round((df['User'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
                        columns={'User': 'User', 'count': 'Percentage'}))
                with col2:
                    fig, ax = plt.subplots()
                    ax.bar(name, count)
                    ax.set_xlabel("Users")
                    ax.set_ylabel("Message Sent")
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)

            # Emoji Analysis
            emojiDF = functions.getEmoji(df)
            st.title("Emoji Analysis")
            col1, col2 = st.columns(2)

            with col1:
                st.dataframe(emojiDF)
            with col2:
                fig, ax = plt.subplots()
                ax.pie(emojiDF[1].head(), labels=emojiDF[0].head(), autopct="%0.2f", shadow=True)
                plt.legend()
                st.pyplot(fig)

            # Most Common Words
            commonWord = functions.MostCommonWords(df)
            fig, ax = plt.subplots()
            ax.bar(commonWord[0], commonWord[1])
            ax.set_xlabel("Words")
            ax.set_ylabel("Frequency")
            plt.xticks(rotation='vertical')
            st.title('Most Frequent Words Used In Chat')
            st.pyplot(fig)

            # Monthly Timeline
            timeline = functions.getMonthlyTimeline(df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['Message'])
            ax.set_xlabel("Month")
            ax.set_ylabel("Messages Sent")
            plt.xticks(rotation='vertical')
            st.title('Monthly Timeline')
            st.pyplot(fig)

            # Daily Timeline
            functions.dailytimeline(df)

            # Most Busy Days
            st.title('Most Busy Days')
            functions.WeekAct(df)

            # Most Busy Months
            st.title('Most Busy Months')
            functions.MonthAct(df)

            # Word Cloud
            st.title("Word Cloud")
            df_wc = functions.create_wordcloud(df)
            fig, ax = plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)

            # Weekly Activity Map
            st.title("Weekly Activity Map")
            user_heatmap = functions.activity_heatmap(df)
            fig, ax = plt.subplots()
            ax = sns.heatmap(user_heatmap)
            st.pyplot(fig)

    except Exception as e:
        st.subheader("Unable to Process Your Request")

