import re
from collections import Counter
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import urlextract
import emoji
from wordcloud import WordCloud

# Function to generate a DataFrame from WhatsApp chat data
def generateDataFrame(file):
    data = file.read().decode("utf-8")
    # Preprocess data
    data = data.replace('\u202f', ' ')
    data = data.replace('\n', ' ')
    
    # Regular expression pattern to split messages based on date-time
    dt_format = '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?(?:AM\s|PM\s|am\s|pm\s)?-\s'
    msgs = re.split(dt_format, data)[1:]
    date_times = re.findall(dt_format, data)

    date = []
    time = []
    
    # Extract date and time from date_times
    for dt in date_times:
        date.append(re.search('\d{1,2}/\d{1,2}/\d{2,4}', dt).group())
        time.append(re.search('\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?', dt).group())

    users = []
    message = []

    # Split messages into user and message parts
    for m in msgs:
        s = re.split('([\w\W]+?):\s', m)
        if (len(s) < 3):
            users.append("Notifications")
            message.append(s[0])
        else:
            users.append(s[1])
            message.append(s[2])

    # Create a DataFrame
    df = pd.DataFrame(list(zip(date, time, users, message)), columns=["Date", "Time(U)", "User", "Message"])
    return df

# Function to extract unique users from the DataFrame
def getUsers(df):
    users = df['User'].unique().tolist()
    users.sort()
    users.remove('Notifications')
    users.insert(0, 'Everyone')
    return users

# Function to preprocess the DataFrame
def PreProcess(df, dayf):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=dayf)
    df['Time'] = pd.to_datetime(df['Time(U)']).dt.time
    df['year'] = df['Date'].apply(lambda x: int(str(x)[:4]))
    df['month'] = df['Date'].apply(lambda x: int(str(x)[5:7]))
    df['date'] = df['Date'].apply(lambda x: int(str(x)[8:10]))
    df['day'] = df['Date'].apply(lambda x: x.day_name())
    df['hour'] = df['Time'].apply(lambda x: int(str(x)[:2]))
    df['month_name'] = df['Date'].apply(lambda x: x.strftime('%B'))
    return df

# Function to extract various statistics
def getStats(df):
    # Count media messages
    media = df[df['Message'] == "<Media omitted> "]
    media_cnt = media.shape[0]
    df.drop(media.index, inplace=True)
    
    # Count deleted messages
    deleted_msgs = df[df['Message'] == "This message was deleted "]
    deleted_msgs_cnt = deleted_msgs.shape[0]
    df.drop(deleted_msgs.index, inplace=True)

    # Extract links using urlextract
    extractor = urlextract.URLExtract()
    links = []
    for msg in df['Message']:
        x = extractor.find_urls(msg)
        if x:
            links.extend(x)
    links_cnt = len(links)
    
    # Count total words and messages
    word_list = []
    for msg in df['Message']:
        word_list.extend(msg.split())
    word_count = len(word_list)
    msg_count = df.shape[0]
    
    return df, media_cnt, deleted_msgs_cnt, links_cnt, word_count, msg_count

# Function to extract and count emojis
def getEmoji(df):
    emojis = []
    for message in df['Message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
    return pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))

# Function to create a monthly message timeline
def getMonthlyTimeline(df):
    df.columns = df.columns.str.strip()
    df = df.reset_index()
    timeline = df.groupby(['year', 'month']).count()['Message'].reset_index()
    time = []
    for i in range(timeline.shape[0]):
        time.append(str(timeline['month'][i]) + "-" + str(timeline['year'][i]))
    timeline['time'] = time
    return timeline

# Function to find and display the most common words
def MostCommonWords(df):
    f = open('stopwords.txt')
    stop_words = f.read()
    f.close()
    words = []
    for message in df['Message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)
    return pd.DataFrame(Counter(words).most_common(20))

# Function to generate a daily timeline and display it using Streamlit
def dailytimeline(df):
    df['taarek'] = df['Date']
    daily_timeline = df.groupby('taarek').count()['Message'].reset_index()
    fig, ax = plt.subplots()
    ax.plot(daily_timeline['taarek'], daily_timeline['Message'])
    ax.set_ylabel("Messages Sent")
    st.title('Daily Timeline')
    st.pyplot(fig)

# Function to create a bar chart of weekly message activity
def WeekAct(df):
    x = df['day'].value_counts()
    fig, ax = plt.subplots()
    ax.bar(x.index, x.values)
    ax.set_xlabel("Days")
    ax.set_ylabel("Message Sent")
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

# Function to create a bar chart of monthly message activity
def MonthAct(df):
    x = df['month_name'].value_counts()
    fig, ax = plt.subplots()
    ax.bar(x.index, x.values)
    ax.set_xlabel("Months")
    ax.set_ylabel("Message Sent")
    plt.xticks(rotation='vertical')
    st.pyplot(fig)

# Function to create an activity heatmap
def activity_heatmap(df):
    period = []
    for hour in df[['day', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period
    user_heatmap = df.pivot_table(index='day', columns='period', values='Message', aggfunc='count').fillna(0)
    return user_heatmap

# Function to create a word cloud
def create_wordcloud(df):
    f = open('stopwords.txt', 'r')
    stop_words = f.read()
    f.close()
    
    # Function to remove stop words from messages
    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in stop_words:
                y.append(word)
        return " ".join(y)

    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
    df['Message'] = df['Message'].apply(remove_stop_words)
    df_wc = wc.generate(df['Message'].str.cat(sep=" "))
    return df_wc

# The main part of your Streamlit app can call these functions and create the desired visualizations and analysis.

