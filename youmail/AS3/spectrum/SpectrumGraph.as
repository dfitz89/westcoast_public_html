package spectrum{
	import flash.display.*
	import flash.text.*
	import flash.events.*
	import flash.media.*
	import flash.net.*
	import flash.filters.*
	import flash.geom.*
	import flash.utils.*
	public class SpectrumGraph extends Sprite{
		private var _spectrumBMP:BitmapData;
		private var MV:MovieClip
		private var bitmap:Bitmap
		public function SpectrumGraph(mv:MovieClip){
			_spectrumBMP =  new BitmapData(mv.width,mv.height,true,0x00000000)
			MV = mv
			 bitmap = new Bitmap(_spectrumBMP)
			bitmap.filters = [new DropShadowFilter(3,45,0xFFFFFF,1,
												   3,2,.3,3)];
			mv.addChild(bitmap)
												
		}
		public function update():void{
			var sp:ByteArray =  new ByteArray()
			SoundMixer.computeSpectrum(sp)
			_spectrumBMP.fillRect(_spectrumBMP.rect, 0x00000000)
			_spectrumBMP.fillRect(new Rectangle(0,0,MV.width,MV.height),0x00000000)
			
			for(var i:int=0;  i<256; i++){
				_spectrumBMP.setPixel32(i*1.34,45+ sp.readFloat()* 60,0xFFFFFFFF)
			}
			
			for(var j:int=0;  j<256; j++){
				_spectrumBMP.setPixel32(j*1.34,110 + sp.readFloat()* 60,0xFFFFFFFF)
			}
			
		}
		public function del():void{
			MV.removeChild(bitmap)
		}
	}
	
}