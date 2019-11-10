**Осторожно!** При прохождении относительно малых групп с использованием --post-count=0 (оставление только лишь постов), капча может долгое время не запрашиваться, что чревато выбросом ошибки Flood Control. Появление Flood Control однажды может привести к бану аккаунта навсегда (проверено на собственном опыте)

### Алгоритм
```
     Поиск групп по ключевому слову "добавь".
     Разделение групп по привелегиям на размещение,
     отсечение групп с запретами на любое размещение/закрытых групп.
		|
		v
+--> Прохождение по каждой Группе; проверка постов группы
|    на размещение в них комментариев и размещение в них комментариев, 
|    если это возможно; оставление постов в группе, если есть на это привелегия;
|    (посты могут меняться очень быстро, поэтому плохая идея -
|    заранее составлять список доступных постов для комментирования)
|		|
|		v
+-- Добавление всех заявок в друзья
```

### Параметры
```
  -h, --help                 	show this help message and exit  
  -a, --add                  	only accept friend requests  
  -V, --version               	show program's version number and exit  
  -l, --list-groups          	print list of groups found  
  -k string, --keyword string 	set keyword for searching groups  
  -m string, --message string 	set default message to post and comment  
  -g int, --group-count int   	set maximum number of groups  
  -p int, --post-count int    	set number of posts for commenting in one group  
  -o int, --offset int        	set offset of group list  
```
