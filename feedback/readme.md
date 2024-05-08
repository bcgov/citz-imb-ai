# Feedback application

This folder contains the infrastructure to improve the A.I by using human feedback in the loop. The feedback curretnly uses trulens to collect and store the data. 

## Embedding Adaptors
One of the methods to improve the A.I espeically in a R.A.G application is to use embedding adaptors. Embedding adaptors is a custom neural network that works alogin side the existing model to improve the embedding search. 

To get the embedding adaptors to work, we have created a frontend application to track the queries, the top K results from the semantic search and the feedback from the user. The feedback is then stored in the trulens database.

Once the feedback is collected, we can use the feedback to train the embedding adaptors.
