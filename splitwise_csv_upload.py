import pandas as pd
from google.colab import userdata
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import User, ExpenseUser

consumer_key = userdata.get('SPLITWISE_CONSUMER_KEY')
consumer_secret = userdata.get('SPLITWISE_CONSUMER_SECRET')
api_key = userdata.get('SPLITWISE_API_KEY')

s = Splitwise(consumer_key, consumer_secret, api_key=api_key)

# Load file 
df = pd.read_csv('change_this_file_path.csv')

df['Posted Date'] = pd.to_datetime(df['Posted Date'])

df['Paid Amount'] = df['Paid Amount'].str.replace('$', '').astype(float)
df['Payer Owes'] = df['Payer Owes'].str.replace('$', '').astype(float)
df['Owed Amount'] = df['Owed Amount'].str.replace('$', '').astype(float)

# Need to figure out a more graceful way to do this, but this kinda works in a notebook - just iteratively check to make sure 2 digit checksum matches paid amount or else it will throw an error when creating expense
df['checksum'] = df['Payer Owes'] + df['Owed Amount']
df['checksum_greater'] = df['checksum'] > df['Paid Amount']
df['checksum_less'] = df['checksum'] < df['Paid Amount']

df # Subtract 0.01 from 'Owed Amount' where 'checksum' greater than 'Paid Amount'
df.loc[df['checksum_greater'], 'Owed Amount'] = df.loc[df['checksum_greater'], 'Owed Amount'] - 0.01

df['checksum'] = df['Payer Owes'] + df['Owed Amount']
df['checksum_greater'] = df['checksum'] > df['Paid Amount']
df['checksum_less'] = df['checksum'] < df['Paid Amount']

# If you want to subtract from original payer
df.loc[df['checksum_greater'], 'Paid Amount'] = df.loc[df['checksum_greater'], 'Paid Amount'] - 0.01

df['checksum'] = df['Payer Owes'] + df['Owed Amount']
df['checksum_greater'] = df['checksum'] > df['Paid Amount']
df['checksum_less'] = df['checksum'] < df['Paid Amount']

# If for some reason it still doesn't match, but noticing that can be rounding issues that flag error here but work when visually inspecting in notebook 
df.loc[df['checksum_greater'], 'Owed Amount'] = df.loc[df['checksum_greater'], 'Owed Amount'] - 0.01
df['checksum'] = df['Payer Owes'] + df['Owed Amount']
df['checksum_greater'] = df['checksum'] > df['Paid Amount']
df['checksum_less'] = df['checksum'] < df['Paid Amount']


# Create expenses based on columns in CSV -- note that this assumes only one other ower! 
for index, row in df.iterrows():
    expense = Expense()

    expense.setGroupId(row['Group ID'])
    expense.setCost(str(row['Paid Amount']))
    expense.setDescription(row['Description'])
    expense.setDate(row['Posted Date'])
    expense.setDetails('Uploaded via API')

    payer = ExpenseUser()
    payer.setId(row['Who Paid'])
    payer.setPaidShare(row['Paid Amount'])
    payer.setOwedShare(row['Payer Owes'])

    ower = ExpenseUser()
    ower.setId(row['Who Else Owes'])
    ower.setOwedShare(row['Owed Amount'])

    expense.addUser(payer)
    expense.addUser(ower)

    # Create the expense in Splitwise
    nExpense, errors = s.createExpense(expense)
    if errors:
        print(f"Error creating expense for {row['Description']}: {errors.getErrors()}")
    else:
        print(f"Expense created successfully: {nExpense.getId()}")

