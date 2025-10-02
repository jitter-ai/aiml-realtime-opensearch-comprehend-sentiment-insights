# 🕵️ AI/ML Real-Time OpenSearch + Comprehend — Sentiment Insights

![Architecture Diagram](./assets/asset_view.png)

---

## 🔮 Coming Soon
This project is being converted from **CloudFormation** to **Terraform** for more flexible, modular, and repeatable deployments.

---

## 📖 Overview
Investigative, real-time sentiment analytics across streaming social content. Text is enriched with [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) and made searchable in [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/) with secure access via [Amazon Cognito](https://docs.aws.amazon.com/cognito/). Infrastructure is automated with Terraform for repeatability and scale.

This repository showcases an **end-to-end AWS pipeline** for near real-time and event-driven sentiment analysis patterns:

| Pipeline | Purpose | Data Source | Processing Mode | Output |
|----------|---------|-------------|-----------------|--------|
| Twitter Sentiment Insights | Monitor live public conversations (hashtags / keywords) | X (Twitter) API streaming (and optional S3 batch) | Real-time streaming (Kinesis) | Indexed documents + dashboards in OpenSearch |

Key highlights:
* Real-time or near real-time sentiment enrichment
* Scalable ingestion (streaming)
* Secure dashboard access with Cognito
* Infrastructure-as-Code for reproducibility

---

## 🔎 Why this matters

* **Investigative analysis:** Monitor social narratives continuously.
* **Sentiment at scale:** Thousands of text records automatically classified (Positive, Negative, Neutral, Mixed) with confidence scores.
* **Actionable insights:** OpenSearch Dashboards enable filtering by topic, timeframe, or sentiment distribution.
* **Enterprise-ready:** IAM, Cognito, CloudWatch, and optional KMS integration.

---

## ⚙️ Architecture Summary — Twitter Streaming (Real-Time)

1. **Collect Tweets** – Stream by hashtag / keyword via [X (Twitter) API](https://developer.x.com/en/docs/x-api) or optionally drop historical CSV/JSON into S3.
2. **Process & Classify** – Lambda functions normalize text and call Comprehend for sentiment.
3. **Stream & Deliver** – Kinesis Data Streams → Kinesis Data Firehose deliver enriched items to OpenSearch.
4. **Search & Visualize** – OpenSearch + Cognito-authenticated dashboards.
5. **Observe & Secure** – CloudWatch Logs, IAM, optional KMS.

---

## 🛠 AWS Services Used

| Service | Role |
|---------|------|
| Amazon S3 | Input datasets (historical tweets if batch) |
| Amazon SQS | Buffer layer for S3 event notifications |
| Amazon EventBridge | Event routing / orchestration |
| AWS Lambda | Text processing, Comprehend integration, index/bootstrap logic |
| Amazon Comprehend | Sentiment classification |
| Amazon Kinesis Data Streams | Real-time ingestion (Twitter pipeline) |
| Amazon Kinesis Data Firehose | Delivery into OpenSearch |
| Amazon OpenSearch Service | Search + dashboards |
| Amazon Cognito | Secure analyst access |
| Amazon CloudWatch | Centralized logging / metrics |
| AWS KMS (optional) | Encryption of data at rest / secrets |

---

## 📈 Demo Scenario

* **Twitter Insight** – Track `#AIRegulation` tweets in real time; visualize shifts in Positive vs. Negative tone.

