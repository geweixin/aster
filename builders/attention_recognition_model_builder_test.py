import tensorflow as tf
from google.protobuf import text_format

from aster.builders import model_builder
from aster.protos import model_pb2


class AttentionRecognitionModelBuilderTest(tf.test.TestCase):

  def test_build_attention_model_single_branch(self):
    model_text_proto = """
    attention_recognition_model {
      feature_extractor {
        convnet {
          crnn_net {
            net_type: SINGLE_BRANCH
            conv_hyperparams {
              op: CONV
              regularizer { l2_regularizer { weight: 1e-4 } }
              initializer { variance_scaling_initializer { } }
              batch_norm { }
            }
            summarize_activations: false
          }
        }
        bidirectional_rnn {
          fw_bw_rnn_cell {
            lstm_cell {
              num_units: 256
              forget_bias: 1.0
              initializer { orthogonal_initializer {} }
            }
          }
          rnn_regularizer { l2_regularizer { weight: 1e-4 } }
          num_output_units: 256
          fc_hyperparams {
            op: FC
            activation: RELU
            initializer { variance_scaling_initializer { } }
            regularizer { l2_regularizer { weight: 1e-4 } }
          }
        }
        summarize_activations: true
      }

      predictor {
        name: "ForwardPredictor"
        bahdanau_attention_predictor {
          reverse: false
          rnn_cell {
            lstm_cell {
              num_units: 256
              forget_bias: 1.0
              initializer { orthogonal_initializer { } }
            }
          }
          rnn_regularizer { l2_regularizer { weight: 1e-4 } }
          num_attention_units: 128
          max_num_steps: 10
          multi_attention: false
          beam_width: 1
          reverse: false
          label_map {
            character_set {
              text_string: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
              delimiter: ""
            }
            label_offset: 2
          }
          loss {
            sequence_cross_entropy_loss {
              sequence_normalize: false
              sample_normalize: true
            }
          }
        }
      }
    }
    """
    model_proto = model_pb2.Model()
    text_format.Merge(model_text_proto, model_proto)
    model_object = model_builder.build(model_proto, True)

    test_groundtruth_text_list = [
      tf.constant(b'hello', dtype=tf.string),
      tf.constant(b'world', dtype=tf.string)]
    model_object.provide_groundtruth(test_groundtruth_text_list)
    test_input_image = tf.random_uniform(
      shape=[2, 32, 100, 3], minval=0, maxval=255,
      dtype=tf.float32, seed=1)
    prediction_dict = model_object.predict(model_object.preprocess(test_input_image))
    loss = model_object.loss(prediction_dict)

    with self.test_session() as sess:
      sess.run([
        tf.global_variables_initializer(),
        tf.tables_initializer()])
      outputs = sess.run({'loss': loss})
      print(outputs['loss'])


if __name__ == '__main__':
  tf.test.main()
