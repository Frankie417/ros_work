# 视觉原始结果

data/week5_test_records.csv为28次原识别记录，22 correct、6 incorrect；两轮8次分拣记录.csv为人工观察，week6_action_log.csv为44条调试日志，二者尚未逐条对应。bin_map.csv是原记录，主Notebook使用自身内联桶位表。

images/week5_evidence保留20组raw/result/masks，共60张；report_week5、report_week6及camera_diagnostics为报告图与诊断截图。报告图片不增加实验样本数。

主Notebook新输出写入runtime/week5、runtime/week6，不追加到data中的原CSV。
