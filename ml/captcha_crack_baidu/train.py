# coding=utf-8

from ml.captcha_crack_baidu.captcha_gen import CHAR_SET
from ml.captcha_crack_baidu.captcha_gen import gen_captcha

from PIL import Image

import numpy as np
import tensorflow as tf
import os
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

import app.logger.logger as logger

# 当前文件所在目录
root_path = os.path.split(os.path.realpath(__file__))[0]

# 训练数据数字基本图片目录
MODEL_PATH = root_path + '/models/'

CHAR_SET_LEN = len(CHAR_SET)
logger.info("验证码文本集合长度 {0} 集合：{1}".format(CHAR_SET_LEN, CHAR_SET))

CAPTCHA_TEXT, IMAGE = gen_captcha()
logger.info("验证码图像channel: {0}".format(IMAGE.shape))  # (60, 160, 3)
#  图像大小
IMAGE_HEIGHT, IMAGE_WIDTH, a = IMAGE.shape
CAPTCHA_TEXT_LEN = len(CAPTCHA_TEXT)
logger.info("验证码文本字符数 ".format(CAPTCHA_TEXT_LEN))  # 验证码最长4字符

####################################################################
X = tf.placeholder(tf.float32, [None, IMAGE_HEIGHT * IMAGE_WIDTH])
Y = tf.placeholder(tf.float32, [None, CAPTCHA_TEXT_LEN * CHAR_SET_LEN])
keep_prob = tf.placeholder(tf.float32)  # dropout


# 把彩色图像转为灰度图像（色彩对识别验证码没有什么用）
def convert2gray(img):
    if len(img.shape) > 2:
        gray = np.mean(img, -1)
        # 上面的转法较快，正规转法如下
        # r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
        # gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return gray
    else:
        return img


""""
cnn在图像大小是2的倍数时性能最高, 如果你用的图像大小不是2的倍数，可以在图像边缘补无用像素。
np.pad(image,((2,3),(2,2)), 'constant', constant_values=(255,))  # 在图像上补2行，下补3行，左补2行，右补2行
"""


# 文本转向量
def text2vec(text):
    text_len = len(text)
    if text_len > CAPTCHA_TEXT_LEN:
        raise ValueError('验证码最长4个字符')

    vector = np.zeros(CAPTCHA_TEXT_LEN * CHAR_SET_LEN)

    def get_char_pos(c):
        for pos, char in enumerate(CHAR_SET):
            if c == char:
                return pos

    for i, c in enumerate(text):
        idx = i * CHAR_SET_LEN + get_char_pos(c)
        vector[idx] = 1
    return vector


# 向量转回文本
def vec2text(vec):
    char_pos = vec.nonzero()[0]
    text = []
    for i, c in enumerate(char_pos):
        char_idx = c % CHAR_SET_LEN
        char = CHAR_SET[char_idx]
        text.append(char)

    return "".join(text)


# 向量（大小MAX_CAPTCHA*CHAR_SET_LEN）用0,1编码 每63个编码一个字符，这样顺利有，字符也有
def test_vec_text():
    vec = text2vec("Fdfd")
    logger.info(vec)
    text = vec2text(vec)
    logger.info(text)  # Fdfd
    vec = text2vec("Fdhd")
    logger.info(vec)
    text = vec2text(vec)
    logger.info(text)  # Fdhd


# 生成一个训练batch
def get_next_batch(batch_size=128):
    batch_x = np.zeros([batch_size, IMAGE_HEIGHT * IMAGE_WIDTH])
    batch_y = np.zeros([batch_size, CAPTCHA_TEXT_LEN * CHAR_SET_LEN])

    for i in range(batch_size):
        text, image = gen_captcha()
        # log(i, text)
        image = convert2gray(image)

        batch_x[i, :] = image.flatten() / 255  # (image.flatten()-128)/128  mean为0
        batch_y[i, :] = text2vec(text)

    return batch_x, batch_y


# 定义CNN
def crack_captcha_cnn(w_alpha=0.01, b_alpha=0.1):
    x = tf.reshape(X, shape=[-1, IMAGE_HEIGHT, IMAGE_WIDTH, 1])

    # w_c1_alpha = np.sqrt(2.0/(IMAGE_HEIGHT*IMAGE_WIDTH)) #
    # w_c2_alpha = np.sqrt(2.0/(3*3*32))
    # w_c3_alpha = np.sqrt(2.0/(3*3*64))
    # w_d1_alpha = np.sqrt(2.0/(8*32*64))
    # out_alpha = np.sqrt(2.0/1024)

    # 3 conv layer
    w_c1 = tf.Variable(w_alpha * tf.random_normal([3, 3, 1, 32]))
    b_c1 = tf.Variable(b_alpha * tf.random_normal([32]))
    conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
    conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv1 = tf.nn.dropout(conv1, keep_prob)

    w_c2 = tf.Variable(w_alpha * tf.random_normal([3, 3, 32, 64]))
    b_c2 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
    conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv2 = tf.nn.dropout(conv2, keep_prob)

    w_c3 = tf.Variable(w_alpha * tf.random_normal([3, 3, 64, 64]))
    b_c3 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
    conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv3 = tf.nn.dropout(conv3, keep_prob)

    # Fully connected layer
    w_d = tf.Variable(w_alpha * tf.random_normal([8 * 20 * 64, 1024]))
    b_d = tf.Variable(b_alpha * tf.random_normal([1024]))
    dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])
    dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
    dense = tf.nn.dropout(dense, keep_prob)

    w_out = tf.Variable(w_alpha * tf.random_normal([1024, CAPTCHA_TEXT_LEN * CHAR_SET_LEN]))
    b_out = tf.Variable(b_alpha * tf.random_normal([CAPTCHA_TEXT_LEN * CHAR_SET_LEN]))
    out = tf.add(tf.matmul(dense, w_out), b_out)
    # out = tf.nn.softmax(out)
    return out


# 训练
def train_crack_captcha_cnn():
    output = crack_captcha_cnn()
    # loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(output, Y))
    loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=output, labels=Y))
    # 最后一层用来分类的softmax和sigmoid有什么不同？
    # optimizer 为了加快训练 learning_rate应该开始大，然后慢慢衰
    optimizer = tf.train.AdamOptimizer(learning_rate=0.001).minimize(loss)

    predict = tf.reshape(output, [-1, CAPTCHA_TEXT_LEN, CHAR_SET_LEN])
    max_idx_p = tf.argmax(predict, 2)
    max_idx_l = tf.argmax(tf.reshape(Y, [-1, CAPTCHA_TEXT_LEN, CHAR_SET_LEN]), 2)
    correct_pred = tf.equal(max_idx_p, max_idx_l)
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    saver = tf.train.Saver()
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        step = 0
        while True:
            batch_x, batch_y = get_next_batch(64)
            _, loss_ = sess.run([optimizer, loss], feed_dict={X: batch_x, Y: batch_y, keep_prob: 0.75})
            logger.info(step, loss_)

            # 每100 step计算一次准确率
            if step % 100 == 0:
                batch_x_test, batch_y_test = get_next_batch(100)
                acc = sess.run(accuracy, feed_dict={X: batch_x_test, Y: batch_y_test, keep_prob: 1.})
                logger.info(step, acc)
                # 如果准确率大于90%,保存模型,完成训练
                if acc > 0.95:
                    saver.save(sess, MODEL_PATH + 'crack_capcha.model', global_step=step)
                    break

            step += 1


# 识别验证码
def crack_captcha(captcha_image, output, saver):
    # output = crack_captcha_cnn()
    # saver = tf.train.Saver()
    with tf.Session() as sess:
        saver.restore(sess, tf.train.latest_checkpoint(MODEL_PATH))

        predict = tf.argmax(tf.reshape(output, [-1, CAPTCHA_TEXT_LEN, CHAR_SET_LEN]), 2)
        text_list = sess.run(predict, feed_dict={X: [captcha_image], keep_prob: 1})

        text = text_list[0].tolist()
        vector = np.zeros(CAPTCHA_TEXT_LEN * CHAR_SET_LEN)
        i = 0
        for n in text:
            vector[i * CHAR_SET_LEN + n] = 1
            i += 1
        return vec2text(vector)


# 测试批量识别验证码
def test_crack_captcha(count):
    output = crack_captcha_cnn()
    saver = tf.train.Saver()

    correct = 0
    for i in range(count):
        text, image = gen_captcha()
        image = convert2gray(image)
        image = image.flatten() / 255
        predict_text = crack_captcha(image, output, saver)
        if text.lower() == predict_text.lower():
            correct = correct + 1
        logger.info("正确: {}  预测: {}".format(text, predict_text))
        logger.info('总数 ' + str(i) + " 正确 " + str(correct) + ' 准确率：' + str(correct / (i + 1)))


# 测试批量识别验证码，验证码图像从data文件夹中加载
def test_crack_captcha_from_disk():
    output = crack_captcha_cnn()
    saver = tf.train.Saver()

    correct = 0
    total = 0
    Image.LOAD_TRUNCATED_IMAGES = True
    for root, dirs, files in os.walk('E:\\BaiduYunDownload\\3\\'):
        for file in files:
            with Image.open('E:\\BaiduYunDownload\\3\\' + file) as image:
                image_data = np.array(image)
                text = file.replace('.jpg', '')
                image_data = convert2gray(image_data)
                image_data = image_data.flatten() / 255
                predict_text = crack_captcha(image_data, output, saver)
                if text.lower() == predict_text.lower():
                    correct = correct + 1
                    logger.info('正确 ' + str(correct))
                total = total + 1
                logger.info("正确: {}  预测: {}".format(text, predict_text))

    logger.info('总数 ' + str(total) + " 正确 " + str(correct) + ' 准确率：' + str(correct / total))


if __name__ == '__main__':
    # test_vec_text()
    train_crack_captcha_cnn()
    # test_crack_captcha(10000)
    # test_crack_captcha_from_disk()
    pass
