f = open('E:/数据可视化/report/competition_answers.md', 'r', encoding='utf-8')
c = f.read(); f.close()

c = c.replace(
    '`src/charts/TransitionMatrix.jsx`（ECharts 实时渲染）',
    '白底红蓝配色静态配图 → `output/report_images/figA_transition_matrix.png`'
)
c = c.replace(
    '`src/charts/CompositionChart.jsx`（前端实时渲染）',
    '白底红蓝配色静态配图 → `output/report_images/figB_composition.png`'
)

f = open('E:/数据可视化/report/competition_answers.md', 'w', encoding='utf-8')
f.write(c); f.close()
print('done')
