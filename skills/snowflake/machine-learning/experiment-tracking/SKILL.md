---
name: experiment-tracking
description: "This skill contains some example code snippets for running experiment tracking"
---

# Experiment Tracking

## When to Use

You should load in this skill when the user is requesting to do some form of experiment tracking for a machine learning or data science project.
This contains a bunch of code snippets and docs for the API for doing anything the user may request.

## Code Snippets

### Intializing the Experiment

```python
from snowflake.ml.experiment import ExperimentTracking
session.use_database("MY_DATABASE")
session.use_schema("MY_SCHEMA")
exp = ExperimentTracking(session=session)
exp.set_experiment("My_Experiment")
```

### Auto Logging Metrics XGBoost

```python
from xgboost import XGBClassifier
from snowflake.ml.experiment.callback.xgboost import SnowflakeXgboostCallback
from snowflake.ml.model.model_signature import infer_signature

sig = infer_signature(X, y)
callback = SnowflakeXgboostCallback(
    exp, model_name="name", model_signature=sig
)
model = XGBClassifier(callbacks=[callback])
with exp.start_run("my_run"):
    model.fit(X, y, eval_set=[(X, y)])
```

### Auto Logging Metrics Keras

```python
import keras
from snowflake.ml.experiment.callback.keras import SnowflakeKerasCallback
from snowflake.ml.model.model_signature import infer_signature

sig = infer_signature(X, y)
callback = SnowflakeKerasCallback(
    exp, model_name="name", model_signature=sig
)
model = keras.Sequential()
model.add(keras.layers.Dense(1))
model.compile(
    optimizer=keras.optimizers.RMSprop(learning_rate=0.1),
    loss="mean_squared_error",
    metrics=["mean_absolute_error"],
)
with exp.start_run("my_run"):
    model.fit(X, y, validation_split=0.5, callbacks=[callback])
```

#### Auto logging Metrics LightGBM

```python
from lightgbm import LGBMClassifier
from snowflake.ml.experiment.callback.lightgbm import SnowflakeLightgbmCallback
from snowflake.ml.model.model_signature import infer_signature

sig = infer_signature(X, y)
callback = SnowflakeLightgbmCallback(
    exp, model_name="name", model_signature=sig
)
model = LGBMClassifier()
with exp.start_run("my_run"):
    model.fit(X, y, eval_set=[(X, y)], callbacks=[callback])
```

### Manual Metric Logging

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from snowflake.ml.model.model_signature import infer_signature

model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X, Y)

y_pred = model.predict(X)
accuracy = accuracy_score(Y, y_pred)
f1 = f1_score(Y, y_pred, average='weighted')

with exp.start_run("sklearn_random_forest"):
    exp.log_params({"max_depth": 5, "random_state": 42}) # Log Params
    exp.log_metrics({"accuracy": accuracy, "f1_score": f1}) # Log Metrics
```

### Ending a Run

```python
exp.end_run("my_run")
```

### Deleting Information

```python
exp.delete_experiment("my_experiment") # Delete a whole experiement
exp.set_experiment("my_experiment") # Or
exp.delete_run("my_run") # Delete a single run from an experiement
```