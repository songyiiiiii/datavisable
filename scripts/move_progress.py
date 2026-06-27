f = open('E:/数据可视化/src/App.jsx', 'r', encoding='utf-8')
c = f.read(); f.close()

# 找到进度条块
old = c.find('<div className="flex items-center gap-3 px-2 h-[32px] shrink-0">')
end = c.find('</div>', c.find('·24FPS</span>', old)) + 6
progress = c[old:end]
print(f'Progress block: {old}-{end}, len={len(progress)}')

# 删除原位置
c2 = c[:old] + c[end:]

# 插入到切片区之前
insert_before = '<div className="w-full flex gap-1 shrink-0" style={{ height:'
pos = c2.find(insert_before)
c3 = c2[:pos] + progress + '\n\n              ' + c2[pos:]

f = open('E:/数据可视化/src/App.jsx', 'w', encoding='utf-8')
f.write(c3); f.close()
print('done')
