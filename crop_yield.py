# Importing all the required libraries

import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing  import LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error,r2_score

#IMPORTING THE DATASET
datafile=pd.read_csv('/home/rgukt/Downloads/extracted_dataset~/crop_yield.csv')

#CLEAN THE DATA
datafile=datafile[['Region','Soil_Type','Crop','Rainfall_mm','Temperature_Celsius','Yield_tons_per_hectare']]

#Renaming the columns
datafile.columns=['region','soil_type','crop','rainfall','temperature','yield']

# Drop the NaN rows in the original file itself without creating the copy of it
datafile.dropna(inplace=True) 



#Split the columns into features(input) and target(output)
X=datafile[['region','soil_type','crop','rainfall','temperature']]
Y=datafile['yield']   

# Encode categorial data
label_encoders = {}
for col in ['region', 'soil_type', 'crop']:
    le=LabelEncoder()
    X.loc[:, col] = le.fit_transform(X[col])
    label_encoders[col] = le

#Dividing the data into testing and training data by train_test_split()
X_train,X_test,Y_train,Y_test = train_test_split(X,Y, test_size=0.2, random_state=42)

#Train the model using Linear Regression
linear_model=LinearRegression()
linear_model.fit(X_train,Y_train)

#Train the model using Random Forest
random_forest=RandomForestRegressor(n_estimators=1,random_state=42)
random_forest.fit(X_train,Y_train)

# Compute R² scores on test data
r2_linear = linear_model.score(X_test, Y_test)
r2_random = random_forest.score(X_test, Y_test)

print(f"R² Linear Regression: {r2_linear:.4f}")
print(f"R² Random Forest: {r2_random:.4f}")

# Save R² scores along with models
metadata = {
    'r2_linear': r2_linear,
    'r2_random': r2_random
}

with open('metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

with open('linear_model.pkl','wb') as f:
    pickle.dump(linear_model, f)

with open('random_forest.pkl', 'wb') as f:
    pickle.dump(random_forest, f)

with open('label_encoders.pkl', 'wb') as encoder_file:
    pickle.dump(label_encoders, encoder_file)

print("model saved successfully")