//-------------------一、类型，值和变量------------------//
console.log("1.数字------------------------------------")

//js能识别十六进制值，以'0x'或'0X'为前缀
console.log(0xff)//255

//-------------- Number 对象是原始数值的包装对象。--------------//

//当 Number() 和运算符 new 一起作为构造函数使用时，它返回一个新创建的 Number 对象。
var num = new Number(333)
console.log(num.valueOf())

//如果不用 new 运算符，把 Number() 作为一个函数来调用，它将把自己的参数转换成一个原始的数值，并且返回这个值（如果转换失败，则返回 NaN）。
var str = "333"
console.log(Number(str))

//Number还有5个常量属性
//1.可表示的最大的数。
console.log(Number.MAX_VALUE)

//2.可表示的最小的数。
console.log(Number.MIN_VALUE)

//3.非数字值
console.log(Number.NaN)

//4.负无穷大，溢出时返回该值。
console.log(Number.NEGATIVE_INFINITY)

//5.正无穷大，溢出时返回该值。
console.log(Number.POSITIVE_INFINITY)

//Number 对象方法
//toString---把数字转换为字符串，使用指定的基数。
console.log(num.toString())

//toLocaleString---把数字转换为字符串，使用本地数字格式顺序。
console.log(num.toLocaleString())

//toFixed---把数字转换为字符串，结果的小数点后有指定位数的数字。该数字会被舍入，也可以用 0 补足，以便它达到指定的长度。
var num = 12.36
console.log(num.toFixed(1))//12.4

//toExponential---把对象的值转换为指数计数法。


//---------------------------------------------------------//

console.log(1/0)

console.log("------------------------------------------")



