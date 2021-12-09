import json
import pyspark
from pyspark.sql import SQLContext, SparkSession
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.ml.feature import Tokenizer,StopWordsRemover, CountVectorizer,IDF,StringIndexer
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.linalg import Vector
from pyspark.ml import Pipeline
from pyspark.ml.classification import NaiveBayes,LogisticRegression, LinearSVC
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


sc = SparkContext("local[2]", appName="spam")
ssc = StreamingContext(sc, 1)
sql_context = SQLContext(sc)

def RDDtoDf(x):
    spark = SparkSession(x.context)
    if not x.isEmpty():
        y = x.collect()[0]
        z = json.loads(y)
        k = z.values()
        df = spark.createDataFrame(k, schema=['feature0', 'feature1', 'feature2']) 
        df.show()
        data_prep_pipe = Pipeline(stages=[ham_spam_to_num,tokenizer,stopremove,count_vec,idf,clean_up])
        cleaner = data_prep_pipe.fit(df)
        clean_data = cleaner.transform(df)
        clean_data = clean_data.select(['label','features'])
        #clean_data.show()
        models(clean_data)
        

def models(data):
    (training,testing) = data.randomSplit([0.7,0.3])
    model_NB(training,testing)
    model_LR(training,testing)
    model_SVC(training,testing)

def model_NB(training,testing):
    nb = NaiveBayes()    
    spam_predictor = nb.fit(training)
    test_results = spam_predictor.transform(testing)
    test_results.show()
    metric = MulticlassClassificationEvaluator()
    acc = metric.evaluate(test_results)
    eval2 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedPrecision")
    eval3 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedRecall")
    prec = eval2.evaluate(test_results)
    recall = eval3.evaluate(test_results)
    print("Accuracy of model NAIVE BAYES at predicting spam was: {}".format(acc))
    print("Precission of model NAIVE BAYES at predicting spam was: {}".format(prec))
    print("Recall of model NAIVE BAYES at predicting spam was: {}".format(recall))

def model_LR(training,testing):
    lr = LogisticRegression()
    spam_predictor = lr.fit(training)
    test_results = spam_predictor.transform(testing)
    test_results.show()
    metric = MulticlassClassificationEvaluator()
    acc = metric.evaluate(test_results)
    eval2 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedPrecision")
    eval3 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedRecall")
    prec = eval2.evaluate(test_results)
    recall = eval3.evaluate(test_results)
    print("Accuracy of model LINEAR REGRESSION at predicting spam was: {}".format(acc))
    print("Precission of model LINEAR REGRESSION at predicting spam was: {}".format(prec))
    print("Recall of model LINEAR REGRESSION at predicting spam was: {}".format(recall))

def model_SVC(training,testing):
    svc = LinearSVC(maxIter = 10, regParam=0.1)
    spam_predictor = svc.fit(training)
    test_results = spam_predictor.transform(testing)
    test_results.show()
    metric = MulticlassClassificationEvaluator()
    acc = metric.evaluate(test_results)
    eval2 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedPrecision")
    eval3 = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedRecall")
    prec = eval2.evaluate(test_results)
    recall = eval3.evaluate(test_results)
    print("Accuracy of model SVC at predicting spam was: {}".format(acc))
    print("Precission of model SVC at predicting spam was: {}".format(prec))
    print("Recall of model SVC at predicting spam was: {}".format(recall))

tokenizer = Tokenizer(inputCol="feature1", outputCol="token1")
stopremove = StopWordsRemover(inputCol='token1',outputCol='stop_token')
count_vec = CountVectorizer(inputCol='stop_token',outputCol='c_vec')
idf = IDF(inputCol="c_vec", outputCol="tf_idf")
ham_spam_to_num = StringIndexer(inputCol='feature2',outputCol='label')
clean_up = VectorAssembler(inputCols=['tf_idf'],outputCol='features')



records = ssc.socketTextStream("localhost", 6100)
if records:
    records.foreachRDD(lambda x: RDDtoDf(x))
ssc.start()
ssc.awaitTermination()
ssc.stop()

#python3 stream.py -f spam -b 20