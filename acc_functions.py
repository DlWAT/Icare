
from ahrs.filters.ekf import EKF
from ahrs.common.quaternion import Quaternion
quaternion_arr = EKF(acc=acc_data, gyr=gyr_data).Q
rotated_acc = [Quaternion(q_np).rotate(acc_data[q_idx]) for q_idx, q_np in enumerate(quaternion_arr)]


def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return w, x, y, z

def qq_mult(q1, q2):
    #q2 = (0.0,) + v1
    return q_mult(q_mult(q1, q2), q_conjugate(q1))
# Conjugate for quaternion
def q_conjugate(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def get_data(n):
    time,quat=get_arc_quat(n)
    time,acc=get_arc_acc(n)
    cquat=get_mult_quat_DFxV(quat)
    cacc=get_rotation_DFxDF(cquat,acc,['accx','accy','accz'])
    
def get_arc_quat(acc_data,gyr_data,time):
    quat = EKF(acc=acc_data, gyr=gyr_data).Q
    return time,quat

def get_arc_acc():
    time= 3#t1
    acc=[0,0,0]#[ax,ay,az]
    return time,acc


def get_mult_quat_DFxV (quat):
    res = pd.DataFrame([],columns=quat.columns.to_numpy())
    q2 = quat.loc[0]
    n=q2[0]**2+q2[1]**2+q2[2]**2+q2[3]**2
    q2=q_conjugate(q2)/n
    for i in range(len(quat)):
        q=quat.loc[i].to_numpy()
        res.loc[i] = q_mult(q2,q)
    return res