This dataset is the result of experiment in U-Space communication comparing push-pull protocol that represented by the REST-API (Representational State Transfer - Application Program Interface) and publisher-subscriber protocol that represented by AMQP (Advanced Message Queuing Protocol).

The dataset is structured in CSV files consisting parameters: sending timestamp, received timestamp, latency, and acknowledgement message in 100 lines of data. The filename represent the interval and message size used in the experiment. It is categorized into API and AMQP folders, then datetime of the experiment.

The python codes to run the experiments are also available here, but you need to update the link to use your own destination server and broker.

Further information about the experiment and information extracted from the dataset can be found in the manuscript with title: "Analysis of Communication Latency in U-Space system using Push-Pull and Publisher-Subscriber Protocols" via this link: http://dx.doi.org/10.13140/RG.2.2.18747.94240

The result was presented at the 1st International Conference on Drones and Unmanned Systems (DAUS' 2025), 19-21 February 2025 in Granada, Spain. You can watch the presentation video via this link: https://www.youtube.com/watch?v=HSSktZhPtpE

The research is part of AI4HyDrop project and supported by the SESAR 3 Joint Undertaking and its founding members and co-funded by the EU’s research and innovation programme Horizon Europe under Grant Agreement no 101114805.

In addition, two data folders are added to facilitate analysis of two more protocol which are ZeroMQ (ZMQ) and Message Queuing Telemetry Transport (MQTT). A new publication is planned to included the additional data into the Electronics journal.
