import mxnet as mx
import numpy as np

from sampler import *
from utils import *

########### model parameters and configurations
# sampler related args
K = 20
beta = 0.1
iter_num = 20
top_words = 10

# file related args
meta_filename = "../preprocess/meta_feature"
word_filename = "../preprocess/word_feature2"

doc_size = 1000
meta_size = 3773


########## configure NN symbolic
## NN configuration with mxnet
dev = mx.cpu()
batch_size = 100

# input
meta = mx.symbol.Variable('meta')
# first layer, num_hidden is 2*K in order not to lose information
w1 = mx.symbol.Variable('w1')
fc1 = mx.symbol.FullyConnected(data=meta,weight=w1,name='fc1',num_hidden=2*K)
act1 = mx.symbol.Activation(data=fc1,name='act1',act_type="tanh")
# second layer, num_hidden is K, output is alpha, output is positive
w2 = mx.symbol.Variable('w2')
fc2 = mx.symbol.FullyConnected(data=act1,weight=w2,name='fc2',num_hidden=K)
act2 = mx.symbol.Activation(data=fc2,name='act2',act_type="sigmoid")
## using softmax to avoid 'explosion'
#output = mx.symbol.Softmax(data=act2,name='alphann')

## bind the layers with exexcutor
# the arg includes meta, w1, fc1_bias, w2, fc2_bias
# record the figure size
meta_shape = (doc_size, meta_size)
arg_shape, out_shape, aux_shape = act2.infer_shape(meta=meta_shape)
print(dict(zip(act2.list_arguments(), arg_shape)))
print(out_shape)

# add meta data as input
meta_origin = load_meta_data(meta_filename, doc_size, meta_size)
meta_input = mx.nd.array(meta_origin)
meta_grad = mx.nd.zeros((1000,3773))

# init other weight
w1_input = mx.nd.empty((40,3773))
w1_input[:] = np.random.uniform(-2.0, 2.0, (40,3773))
w1_grad = mx.nd.zeros((40,3773))
w2_input = mx.nd.empty(((20,40)))
w2_input[:] = np.random.uniform(-2.0, 2.0, (20,40))
w2_grad = mx.nd.zeros((20,40))
b1_input = mx.nd.empty(((40,)))
b1_input[:] = np.random.uniform(-1.0, 1.0, (40,))
b1_grad = mx.nd.zeros((40,))
b2_input = mx.nd.empty(((20,)))
b2_input[:] = np.random.uniform(-1.0, 1.0, (20,))
b2_grad = mx.nd.zeros((20,))

# bind with executor
args = dict()
args['meta'] = meta_input
args['w1'] = w1_input
args['w2'] = w2_input
args['fc1_bias'] = b1_input
args['fc2_bias'] = b2_input

grads = dict()
grads['meta'] = meta_grad
grads['w1'] = w1_grad
grads['w2'] = w2_grad
grads['fc1_bias'] = b1_grad
grads['fc2_bias'] = b2_grad

reqs = ["write" for name in grads]
texec = act2.bind(ctx=dev, args=args, args_grad=grads, grad_req=reqs)

########## EM Framework for updates
# texec forward to get output
texec.forward()
temp = texec.outputs[0].asnumpy()
print(len(temp))
print(len(temp[0]))
print(temp[0][2])

# build a layer with g and backward
gradient_input = mx.nd.empty((1000,20))
gradient_input[:] = np.random.uniform(-1.0, 1.0, (1000,20))
texec.backward(out_grads=gradient_input)

temp = w1_grad.asnumpy()
print(len(temp))
print(len(temp[0]))
print(temp[0][2])





