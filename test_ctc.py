import numpy as np
import theano
import ctc_cost
import theano.tensor as T
from numpy import testing
from itertools import izip, islice


floatX = theano.config.floatX


def test_log_add():
    x = T.scalar()
    y = T.scalar()
    z = ctc_cost._log_add(x, y)
    X = -3.0
    Y = -np.inf
    value = z.eval({x: X, y: Y})
    assert value == -3.0


def test_log_dot_matrix():
    x = T.matrix()
    y = T.matrix()
    z = ctc_cost._log_dot_matrix(y, x)
    X = np.asarray(np.random.normal(0, 1, (5, 4)), dtype=floatX)
    Y = np.asarray(np.random.normal(0, 1, (3, 5)), dtype=floatX)
    #Y = np.ones((3, 5), dtype=floatX) * 3
    value = z.eval({x: X, y: Y})
    np_value = np.log(np.dot(np.exp(Y), np.exp(X)))
    assert np.mean((value - np_value)**2) < 1e5


def test_log_dot_matrix_zeros():
    x = T.matrix()
    y = T.matrix()
    z = ctc_cost._log_dot_matrix(y, x)
    X = np.log(np.asarray(np.eye(5), dtype=floatX))
    Y = np.asarray(np.random.normal(0, 1, (3, 5)), dtype=floatX)
    #Y = np.ones((3, 5), dtype=floatX) * 3
    value = z.eval({x: X, y: Y})
    np_value = np.log(np.dot(np.exp(Y), np.exp(X)))
    assert np.mean((value - np_value)**2) < 1e5


def test_ctc_add_blanks():
    BATCHES = 3
    N_LABELS = 3
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    blanked_y, blanked_y_mask = ctc_cost._add_blanks(
        y=y,
        blank_symbol=1,
        y_mask=y_mask)
    Y = np.zeros((N_LABELS, BATCHES), dtype='int64')
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    Y_mask[-1, 0] = 0
    Blanked_y_mask = blanked_y_mask.eval({y_mask: Y_mask})
    Blanked_y = blanked_y.eval({y: Y})
    assert (Blanked_y == np.array([[1, 1, 1],
                                   [0, 0, 0],
                                   [1, 1, 1],
                                   [0, 0, 0],
                                   [1, 1, 1],
                                   [0, 0, 0],
                                   [1, 1, 1]], dtype='int32')).all()
    assert (Blanked_y_mask == np.array([[1., 1., 1.],
                                        [1., 1., 1.],
                                        [1., 1., 1.],
                                        [1., 1., 1.],
                                        [1., 1., 1.],
                                        [0., 1., 1.],
                                        [0., 1., 1.]], dtype=floatX)).all()


def test_ctc_symmetry_logscale():
    LENGTH = 5000
    BATCHES = 3
    CLASSES = 4
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_cost_t = ctc_cost.cost(y, y_hat, y_mask, y_hat_mask)

    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES), dtype=floatX)
    Y_hat[:, :, 0] = .3
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .4
    Y_hat[:, :, 3] = .1
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    # default blank symbol is the highest class index (3 in this case)
    Y = np.repeat(np.array([0, 1, 2, 1, 2, 0, 2, 2, 2]),
                  BATCHES).reshape((9, BATCHES))
    # the masks for this test should be all ones.
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    forward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y,
                                  y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    backward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y[::-1],
                                   y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    testing.assert_almost_equal(forward_cost[0], backward_cost[0])
    assert not np.isnan(forward_cost[0])
    assert not np.isnan(backward_cost[0])
    assert not np.isinf(np.abs(forward_cost[0]))
    assert not np.isinf(np.abs(backward_cost[0]))


def test_ctc_symmetry():
    LENGTH = 20
    BATCHES = 3
    CLASSES = 4
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_cost_t = ctc_cost.cost(y, y_hat, y_mask, y_hat_mask, log_scale=False)

    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES), dtype=floatX)
    Y_hat[:, :, 0] = .3
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .4
    Y_hat[:, :, 3] = .1
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    # default blank symbol is the highest class index (3 in this case)
    Y = np.repeat(np.array([0, 1, 2, 1, 2, 0, 2, 2, 2]),
                  BATCHES).reshape((9, BATCHES))
    # the masks for this test should be all ones.
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    forward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y,
                                  y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    backward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y[::-1],
                                   y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    testing.assert_almost_equal(forward_cost[0], backward_cost[0])
    assert not np.isnan(forward_cost[0])
    assert not np.isnan(backward_cost[0])
    assert not np.isinf(np.abs(forward_cost[0]))
    assert not np.isinf(np.abs(backward_cost[0]))


def test_ctc_exact_log_scale():
    LENGTH = 4
    BATCHES = 1
    CLASSES = 2
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_cost_t = ctc_cost.cost(y, y_hat, y_mask, y_hat_mask, log_scale=True)

    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES), dtype=floatX)
    Y_hat[:, :, 0] = .7
    Y_hat[:, :, 1] = .3
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    # default blank symbol is the highest class index (3 in this case)
    Y = np.zeros((2, 1), dtype='int64')
    # -0-0
    # 0-0-
    # 0--0
    # 0-00
    # 00-0
    answer = np.log(3 * (.3 * .7)**2 + 2 * .3 * .7**3)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    forward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y,
                                  y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    backward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y[::-1],
                                   y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    assert not np.isnan(forward_cost[0])
    assert not np.isnan(backward_cost[0])
    assert not np.isinf(np.abs(forward_cost[0]))
    assert not np.isinf(np.abs(backward_cost[0]))
    testing.assert_almost_equal(-forward_cost[0], answer)
    testing.assert_almost_equal(-backward_cost[0], answer)


def test_ctc_exact():
    LENGTH = 4
    BATCHES = 1
    CLASSES = 2
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_cost_t = ctc_cost.cost(y, y_hat, y_mask, y_hat_mask, log_scale=False)

    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES), dtype=floatX)
    Y_hat[:, :, 0] = .7
    Y_hat[:, :, 1] = .3
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    # default blank symbol is the highest class index (3 in this case)
    Y = np.zeros((2, 1), dtype='int64')
    # -0-0
    # 0-0-
    # 0--0
    # 0-00
    # 00-0
    answer = np.log(3 * (.3 * .7)**2 + 2 * .3 * .7**3)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    forward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y,
                                  y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    backward_cost = ctc_cost_t.eval({y_hat: Y_hat, y: Y[::-1],
                                   y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    assert not np.isnan(forward_cost[0])
    assert not np.isnan(backward_cost[0])
    assert not np.isinf(np.abs(forward_cost[0]))
    assert not np.isinf(np.abs(backward_cost[0]))
    testing.assert_almost_equal(-forward_cost[0], answer)
    testing.assert_almost_equal(-backward_cost[0], answer)


def test_ctc_log_path_probabs():
    LENGTH = 10
    BATCHES = 3
    CLASSES = 2
    N_LABELS = 3
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    blanked_y, blanked_y_mask = ctc_cost._add_blanks(
        y=y,
        blank_symbol=1,
        y_mask=y_mask)
    p = ctc_cost._log_path_probabs(blanked_y, y_hat, blanked_y_mask, y_hat_mask, 1)
    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES + 1), dtype=floatX)
    Y_hat[:, :, 0] = .7
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .1
    Y = np.zeros((N_LABELS, BATCHES), dtype='int64')
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-2:, 0] = 0
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    forward_probs = p.eval({y_hat: Y_hat, y: Y,
                            y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    assert forward_probs[-2, 0, 0] == -np.inf
    Y_mask[-1] = 0
    forward_probs_y_mask = p.eval({y_hat: Y_hat, y: Y,
                                   y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    assert forward_probs_y_mask[-1, 1, -2] == -np.inf
    assert not np.isnan(forward_probs).any()


def test_ctc_log_forward_backward():
    LENGTH = 8
    BATCHES = 4
    CLASSES = 2
    N_LABELS = 3
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    blanked_y, blanked_y_mask = ctc_cost._add_blanks(
        y=y,
        blank_symbol=1,
        y_mask=y_mask)
    f, b = ctc_cost._log_forward_backward(blanked_y, y_hat,
                                          blanked_y_mask, y_hat_mask, CLASSES)
    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES + 1), dtype=floatX)
    Y_hat[:, :, 0] = .7
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .1
    Y_hat[3, :, 0] = .3
    Y_hat[3, :, 1] = .4
    Y_hat[3, :, 2] = .3
    Y = np.zeros((N_LABELS, BATCHES), dtype='int64')
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-2:] = 0
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    Y_mask[-2:, 0] = 0
    y_prob = ctc_cost._class_batch_to_labeling_batch(blanked_y,
                                                    y_hat,
                                                    y_hat_mask)
    forward_probs = f.eval({y_hat: Y_hat, y: Y,
                            y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    backward_probs = b.eval({y_hat: Y_hat, y: Y,
                            y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    y_probs = y_prob.eval({y_hat: Y_hat, y: Y, y_hat_mask: Y_hat_mask})
    assert not ((forward_probs + backward_probs)[:, 0, :] == -np.inf).all()
    marg = forward_probs + backward_probs - np.log(y_probs)
    forward_probs = np.exp(forward_probs)
    backward_probs = np.exp(backward_probs)
    L = (forward_probs * backward_probs[::-1][:, :, ::-1] / y_probs).sum(2)
    assert not np.isnan(forward_probs).any()


def finite_diff(Y, Y_hat, Y_mask, Y_hat_mask, eps=1e-2, n_steps=None):
    y_hat = T.tensor3('features')
    y_hat_mask = T.matrix('features_mask')
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_cost_t = ctc_cost.cost(y, y_hat, y_mask, y_hat_mask)
    get_cost = theano.function([y, y_hat, y_mask, y_hat_mask],
                               ctc_cost_t.sum())
    diff_grad = np.zeros_like(Y_hat)

    for grad, val in islice(izip(np.nditer(diff_grad, op_flags=['readwrite']),
                                 np.nditer(Y_hat, op_flags=['readwrite'])),
                            0, n_steps):
        val += eps
        error_inc = get_cost(Y, Y_hat, Y_mask, Y_hat_mask)
        val -= 2.0 * eps
        error_dec = get_cost(Y, Y_hat, Y_mask, Y_hat_mask)
        grad[...] = .5 * (error_inc - error_dec) / eps
        val += eps

    return diff_grad


def test_ctc_class_batch_to_labeling_batch():
    LENGTH = 20
    BATCHES = 4
    CLASSES = 2
    LABELS = 2
    y_hat = T.tensor3()
    y_hat_mask = T.matrix('features_mask')
    y = T.lmatrix('phonemes')
    y_labeling = ctc_cost._class_batch_to_labeling_batch(y, y_hat, y_hat_mask)
    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES + 1), dtype=floatX)
    Y = np.zeros((2, BATCHES), dtype='int64')
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-5:] = 0
    Y_labeling = y_labeling.eval({y_hat: Y_hat, y: Y, y_hat_mask: Y_hat_mask})
    assert Y_labeling.shape == (LENGTH, BATCHES, LABELS)


def test_ctc_labeling_batch_to_class_batch():
    LENGTH = 20
    BATCHES = 4
    CLASSES = 2
    LABELS = 2
    y_labeling = T.tensor3()
    y = T.lmatrix('phonemes')
    y_hat = ctc_cost._labeling_batch_to_class_batch(y, y_labeling, CLASSES + 1)
    Y_labeling = np.zeros((LENGTH, BATCHES, LABELS), dtype=floatX)
    Y = np.zeros((2, BATCHES), dtype='int64')
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-5:] = 0
    Y_hat = y_hat.eval({y_labeling: Y_labeling, y: Y})
    assert Y_hat.shape == (LENGTH, BATCHES, CLASSES + 1)


def test_ctc_targets():
    LENGTH = 20
    BATCHES = 4
    CLASSES = 2
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    ctc_target = ctc_cost.get_targets(y, T.log(y_hat), y_mask, y_hat_mask)
    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES + 1), dtype=floatX)
    Y_hat[:, :, 0] = .7
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .1
    Y_hat[3, :, 0] = .3
    Y_hat[3, :, 1] = .4
    Y_hat[3, :, 2] = .3
    Y = np.zeros((2, BATCHES), dtype='int64')
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-5:] = 0
    # default blank symbol is the highest class index (3 in this case)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    target = ctc_target.eval({y_hat: Y_hat, y: Y,
                              y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    # Note that this part is the same as the cross entropy gradient
    grad = -target / Y_hat
    test_grad = finite_diff(Y, Y_hat, Y_mask, Y_hat_mask, eps=1e-2, n_steps=5)
    testing.assert_almost_equal(grad.flatten()[:5],
                                test_grad.flatten()[:5], decimal=3)


def test_ctc_pseudo_cost():
    LENGTH = 500
    BATCHES = 40
    CLASSES = 2
    N_LABELS = 45
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    pseudo_cost = ctc_cost.pseudo_cost_old(y, y_hat, y_mask, y_hat_mask)

    Y_hat = np.zeros((LENGTH, BATCHES, CLASSES + 1), dtype=floatX)
    Y_hat[:, :, 0] = .75
    Y_hat[:, :, 1] = .2
    Y_hat[:, :, 2] = .05
    Y_hat[3, 0, 0] = .3
    Y_hat[3, 0, 1] = .4
    Y_hat[3, 0, 2] = .3
    Y = np.zeros((N_LABELS, BATCHES), dtype='int64')
    Y[25:, :] = 1
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-5:] = 0
    # default blank symbol is the highest class index (3 in this case)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    Y_mask[30:] = 0
    cost = pseudo_cost.eval({y_hat: Y_hat, y: Y,
                             y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    pseudo_grad = T.grad(ctc_cost.pseudo_cost_old(y, y_hat,
                                              y_mask, y_hat_mask).sum(),
                         y_hat)
    #test_grad2 = pseudo_grad.eval({y_hat: Y_hat, y: Y,
    #                               y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    # TODO: write some more meaningful asserts here
    assert cost.sum() > 0

def test_ctc_pseudo_cost_skip_softmax_stability():
    LENGTH = 500
    BATCHES = 40
    CLASSES = 10
    N_LABELS = 45
    y_hat = T.tensor3('features')
    input_mask = T.matrix('features_mask')
    y_hat_mask = input_mask
    y = T.lmatrix('phonemes')
    y_mask = T.matrix('phonemes_mask')
    pseudo_cost = ctc_cost.pseudo_cost_old(y, y_hat, y_mask, y_hat_mask,
                                       skip_softmax=True)

    Y_hat = np.asarray(np.random.normal(0, 1, (LENGTH, BATCHES, CLASSES + 1)),
                       dtype=floatX)
    Y = np.zeros((N_LABELS, BATCHES), dtype='int64')
    Y[25:, :] = 1
    Y_hat_mask = np.ones((LENGTH, BATCHES), dtype=floatX)
    Y_hat_mask[-5:] = 0
    # default blank symbol is the highest class index (3 in this case)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    Y_mask[30:] = 0
    pseudo_grad = T.grad(pseudo_cost.sum(), y_hat)
    test_grad = pseudo_grad.eval({y_hat: Y_hat, y: Y,
                                  y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    y_hat_softmax = T.exp(y_hat) / T.exp(y_hat).sum(2)[:, :, None]
    pseudo_cost2 = ctc_cost.pseudo_cost_old(y, y_hat_softmax, y_mask, y_hat_mask,
                                        skip_softmax=False)
    pseudo_grad2 = T.grad(pseudo_cost2.sum(), y_hat)
    test_grad2 = pseudo_grad2.eval({y_hat: Y_hat, y: Y,
                                    y_hat_mask: Y_hat_mask, y_mask: Y_mask})
    testing.assert_almost_equal(test_grad, test_grad2, decimal=4)


def test_lasagne_ctc():
    import lasagne
    from lasagne.layers import LSTMLayer, InputLayer, DenseLayer,\
        NonlinearityLayer, ReshapeLayer, EmbeddingLayer, RecurrentLayer
    import theano
    import theano.tensor as T
    import numpy as np
    num_batch, input_seq_len = 10, 15
    num_classes = 10
    target_seq_len = 5
    num_rnn_units = 50

    input_seq_len += target_seq_len
    def print_pred(y_hat):
        blank_symbol = num_classes
        res = []
        for i, s in enumerate(y_hat):
            if (s != blank_symbol) and (i == 0 or s != y_hat[i - 1]):
                res += [s]
        if len(res) > 0:
            return "".join(map(str, list(res)))
        else:
            return "-"*target_seq_len

    Y_hat = np.asarray(np.random.normal(
        0, 1, (input_seq_len, num_batch, num_classes + 1)), dtype=floatX)
    Y = np.zeros((target_seq_len, num_batch), dtype='int64')
    Y[25:, :] = 1
    Y_hat_mask = np.ones((input_seq_len, num_batch), dtype=floatX)
    Y_hat_mask[-5:] = 0
    # default blank symbol is the highest class index (3 in this case)
    Y_mask = np.asarray(np.ones_like(Y), dtype=floatX)
    X = np.random.random(
        (num_batch, input_seq_len)).astype('int32')

    y = T.imatrix('phonemes')
    x = T.imatrix()   # batchsize, input_seq_len, features



    # setup Lasagne Recurrent network
    # The output from the network is shape
    #  a) output_lin_ctc is the activation before softmax  (input_seq_len, batch_size, num_classes + 1)
    #  b) ouput_softmax is the output after softmax  (batch_size, input_seq_len, num_classes + 1)
    l_inp = InputLayer((num_batch, input_seq_len))
    l_emb = EmbeddingLayer(l_inp,
                           input_size=num_classes+1,
                           output_size=num_classes+1,
                           W=np.identity(num_classes+1).astype('float32'))
    ini = lasagne.init.Uniform(0.1)
    zero = lasagne.init.Constant(0.0)
    cell = lasagne.init.Uniform(0.1)
    l_rnn = LSTMLayer(l_emb,
                      num_units=num_rnn_units,
                      peepholes=True,
                      W_in_to_ingate=ini,
                      W_hid_to_ingate=ini,
                      b_ingate=zero,
                      W_in_to_forgetgate=ini,
                      W_hid_to_forgetgate=ini,
                      b_forgetgate=zero,
                      W_in_to_cell=ini,
                      W_hid_to_cell=ini,
                      b_cell=zero,
                      W_in_to_outgate=ini,
                      W_hid_to_outgate=ini,
                      b_outgate=zero,
                      cell_init=lasagne.init.Constant(0.),
                      hid_init=lasagne.init.Constant(0.),
                      W_cell_to_forgetgate=cell,
                      W_cell_to_ingate=cell,
                      W_cell_to_outgate=cell)
    l_rnn_shp = ReshapeLayer(l_rnn, (num_batch*input_seq_len, num_rnn_units))
    l_out = DenseLayer(l_rnn_shp, num_units=num_classes+1,
                       nonlinearity=lasagne.nonlinearities.identity)  # + blank

    l_out_shp = ReshapeLayer(l_out, (num_batch, input_seq_len, num_classes+1))

    # dimshuffle to shape format (input_seq_len, batch_size, num_classes + 1)
    #l_out_shp_ctc = lasagne.layers.DimshuffleLayer(l_out_shp, (1, 0, 2))

    l_out_softmax = NonlinearityLayer(
        l_out, nonlinearity=lasagne.nonlinearities.softmax)
    l_out_softmax_shp = ReshapeLayer(
        l_out_softmax, (num_batch, input_seq_len, num_classes+1))

    output_lin_ctc = lasagne.layers.get_output(l_out_shp, x)
    output_softmax = lasagne.layers.get_output(l_out_softmax_shp, x)
    all_params = l_rnn.get_params(trainable=True)  # dont learn embeddingl
    print all_params

    ###############
    #  GRADIENTS  #
    ###############

    # the CTC cross entropy between y and linear output network
    pseudo_cost = ctc_cost.pseudo_cost(
        y, output_lin_ctc)

    # calculate the gradients of the CTC wrt. linar output of network
    pseudo_cost_grad = T.grad(pseudo_cost.sum() / num_batch, all_params)
    true_cost = ctc_cost.cost(y, output_softmax)
    cost = T.mean(true_cost)

    sh_lr = theano.shared(lasagne.utils.floatX(0.01))
    #updates = lasagne.updates.sgd(pseudo_cost_grad, all_params, learning_rate=sh_lr)
    #updates = lasagne.updates.apply_nesterov_momentum(updates, all_params, momentum=0.9)
    updates = lasagne.updates.rmsprop(pseudo_cost_grad, all_params, learning_rate=sh_lr)

    train = theano.function([x, y],
                            [output_lin_ctc, output_softmax, cost, pseudo_cost],
                            updates=updates)


    # Create test dataset
    num_samples = 1000
    np.random.seed(1234)

    # create simple dataset of format
    # input [5,5,5,5,5,2,2,2,2,2,3,3,3,3,3,....,1,1,1,1]
    # targets [5,2,3,...,1]
    # etc...
    input_lst, output_lst = [], []
    for i in range(num_samples):
        this_input = []
        this_output = []
        for j in range(target_seq_len):
            this_class = np.random.randint(num_classes)
            this_input += [this_class]*3 + [num_classes]
            this_output += [this_class]

        this_input += (input_seq_len - len(this_input))*[this_input[-1]]

        input_lst.append(this_input)
        output_lst.append(this_output)
        print this_input, this_output

    input_arr = np.concatenate([input_lst]).astype('int32')
    y_arr = np.concatenate([output_lst]).astype('int32')

    y_mask_arr = np.ones((num_batch, target_seq_len), dtype='float32')
    input_mask_arr = np.ones((num_batch, input_seq_len), dtype='float32')

    for nn in range(10000):
        cost_lst = []
        shuffle = np.random.permutation(num_samples)
        for i in range(num_samples//num_batch):
            idx = shuffle[i*num_batch:(i+1)*num_batch]
            _, output_softmax_val, cost, pseudo_cost_val = train(
                input_arr[idx],
                y_arr[idx])
            output_softmax_lst = output_softmax_val
            labels_lst = y_arr[idx]
            cost_lst += [cost]
            #testing.assert_almost_equal(pseudo_cost, pseudo_cost_old, decimal=4)
            #testing.assert_array_almost_equal(pseudo_cost_val, pseudo_cost_old_val)

        if (nn+1) % 200 == 0:
            DECAY = 1.5
            new_lr = lasagne.utils.floatX(sh_lr.get_value() / DECAY)
            sh_lr.set_value(new_lr)
            print "----------------------->NEW LR:", new_lr

        print nn, "Mean cost:", np.mean(cost_lst)
        if (nn+1) % 4 == 0:
            for jj in range(num_batch):
                pred = print_pred(np.argmax(output_softmax_val[jj], axis=-1))
                true = "".join(map(str, labels_lst[jj]))
                pred += (target_seq_len-len(pred)) * " "
                print pred, true


test_lasagne_ctc()