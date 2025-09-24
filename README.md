# 🕵️ AI/ML Real-Time OpenSearch + Comprehend — Twitter Sentiment Insights

![Architecture Diagram](./assets/architecture.png)

> **Goal:** Investigate public sentiment by automatically streaming text from sources like the [X (Twitter) API](https://developer.x.com/en/docs/x-api) into [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) for classification, and make those enriched insights searchable in [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/). Access is managed securely with [Amazon Cognito](https://docs.aws.amazon.com/cognito/).
> Fully deployed and managed with **Terraform**, this design is built to handle **high-volume, real-time** streaming for investigative, analytic, or monitoring use cases.

---

## Why this matters

* **Investigative analysis:** Track public conversations around events, brands, or topics in real time.
* **Sentiment at scale:** Thousands of tweets can be analyzed automatically, tagged as *Positive, Negative, Neutral, or Mixed*.
* **Actionable insights:** Search and filter inside OpenSearch Dashboards to reveal public mood shifts or anomalies.
* **Enterprise-ready:** Everything is repeatable and scalable with Terraform.

---

## How it works

1. **Collect tweets**

   * Connect to the [X (Twitter) API](https://developer.x.com/en/docs/x-api) to stream tweets by keyword, hashtag, or account.
   * Optionally, drop CSV/JSON datasets into [Amazon S3](https://docs.aws.amazon.com/s3/) for batch analysis.

2. **Trigger & Processing**

   * [Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/) routes new events.
   * [AWS Lambda](https://docs.aws.amazon.com/lambda/) functions clean up tweets and send text to Comprehend.

3. **Sentiment Analysis**

   * [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) classifies each tweet’s tone (Positive, Negative, Neutral, Mixed) and adds confidence scores.

4. **Streaming & Delivery**

   * Results flow through [Amazon Kinesis Data Streams](https://docs.aws.amazon.com/streams/latest/dev/) and into [Amazon Kinesis Data Firehose](https://docs.aws.amazon.com/firehose/) for delivery to OpenSearch.

5. **Search & Dashboards**

   * Enriched tweets are indexed in [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/).
   * Analysts or investigators log in via [Amazon Cognito](https://docs.aws.amazon.com/cognito/) to access secure dashboards.

6. **Monitoring & Security**

   * [Amazon CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/) track pipeline activity.
   * [AWS IAM](https://docs.aws.amazon.com/iam/) ensures controlled permissions.
   * KMS can be used to encrypt sensitive data.

---

## Key Benefits

* 🕵️ **Investigative lens:** Monitor emerging narratives or disinformation campaigns in real time.
* 📊 **Dashboard-ready:** Easily pivot between topics, hashtags, and sentiment distributions.
* ⚡ **High-volume scale:** From a few hundred tweets to continuous firehose ingestion.
* 🛠 **Terraform-based:** Full deployment automation ensures repeatability and consistency.

---

## Demo scenario

* **Investigative example:** Stream tweets with the hashtag `#AIRegulation`. Watch as the pipeline processes them through Comprehend, indexes the results, and displays the changing tone of the conversation in OpenSearch dashboards.
* Analysts can filter by sentiment, timeframe, or keyword to surface trends and anomalies.

---

**Repository name suggestion:**
`aiml-realtime-opensearch-comprehend-sentiment-insights`

**GitHub description (short):**
Investigative real-time AI/ML pipeline: stream tweets via X (Twitter) API, classify sentiment with Amazon Comprehend, and search insights in OpenSearch dashboards. Terraform-managed for scale.
