# 🕵️ AI/ML Real-Time OpenSearch + Comprehend — Sentiment Insights

![Architecture Diagram](./assets/asset_view.png)

---

## 📖 Overview
Investigative, real-time sentiment analytics across streaming social content. Text is enriched with [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) and made searchable in [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/) with secure access via [Amazon Cognito](https://docs.aws.amazon.com/cognito/). Infrastructure is automated with [Terraform](https://www.terraform.io/) for repeatability and scale.

This repository showcases an **end-to-end AWS pipeline** for near real-time sentiment analysis:

| Pipeline | Purpose | Data Source | Processing Mode | Output |
|----------|---------|-------------|-----------------|--------|
| Twitter Sentiment Insights | Monitor live public conversations (hashtags / keywords) | X (Twitter) API or batch CSV uploads to S3 | Event-driven + real-time (Kinesis) | Indexed documents + dashboards in OpenSearch |

Key highlights:
* Real-time sentiment enrichment
* Scalable ingestion (streaming + S3 batch)
* Secure dashboard access with Cognito
* Infrastructure-as-Code for reproducibility

---

## 🔮 Coming Soon
This project is being converted from **CloudFormation** to **Terraform** for more flexible, modular, and repeatable deployments.

---

## 🔎 Why this matters

* **Investigative analysis:** Monitor social narratives continuously.
* **Sentiment at scale:** Thousands of text records automatically classified (Positive, Negative, Neutral, Mixed) with confidence scores.
* **Actionable insights:** OpenSearch Dashboards enable filtering by topic, timeframe, or sentiment distribution.
* **Enterprise-ready:** IAM, Cognito, CloudWatch integration.

---

## ⚙️ Architecture Summary — Twitter / Social Streaming

1. **Ingest Data** – Tweets or social content ingested either directly (API) or via batch drop into [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).
2. **Event Routing** – [Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/what-is-amazon-eventbridge.html) triggers [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) for normalization.
3. **Stream & Enrich** – [Amazon Kinesis Data Streams](https://docs.aws.amazon.com/streams/latest/dev/introduction.html) → [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) classifies sentiment → Enriched Kinesis stream.
4. **Deliver & Index** – [Amazon Kinesis Data Firehose](https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html) writes enriched items into [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/).
5. **Search & Visualize** – [Amazon Cognito](https://docs.aws.amazon.com/cognito/) provides secure dashboard access for analysts.
6. **Observe & Secure** – [Amazon CloudWatch](https://docs.aws.amazon.com/cloudwatch/) logs/metrics; [AWS Key Management Service (KMS)](https://docs.aws.amazon.com/kms/) optional for encryption.

---

## 🛠 AWS Services Used

| Service | Role |
|---------|------|
| [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) | Input datasets (historical tweet CSVs) |
| [Amazon EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/what-is-amazon-eventbridge.html) | Event routing / orchestration |
| [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) | Data normalization, Comprehend calls |
| [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/how-sentiment.html) | Sentiment classification |
| [Amazon Kinesis Data Streams](https://docs.aws.amazon.com/streams/latest/dev/introduction.html) | Real-time ingestion pipeline |
| Enriched Kinesis Data Streams | Holds sentiment-tagged events |
| [Amazon Kinesis Data Firehose](https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html) | Delivery into OpenSearch |
| [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/) | Search + dashboards |
| [Amazon Cognito](https://docs.aws.amazon.com/cognito/) | Secure analyst access |
| [Amazon CloudWatch](https://docs.aws.amazon.com/cloudwatch/) | Centralized logging / metrics |
| [AWS KMS (optional)](https://docs.aws.amazon.com/kms/) | Encryption of data at rest / secrets |

---

## 📈 Demo Scenario

* **Twitter Insight** – Track `#AIRegulation` tweets in real time; visualize shifts in Positive vs. Negative tone.

